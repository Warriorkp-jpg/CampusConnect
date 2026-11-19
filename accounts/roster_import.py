import csv
import io
import re
from decimal import Decimal, InvalidOperation

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from openpyxl import load_workbook

from .models import StudentRoster


MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 5000
REQUIRED_COLUMNS = {"roll_number", "full_name"}
OPTIONAL_COLUMNS = {"college_email", "program", "batch", "cgpa", "backlogs"}
HEADER_ALIASES = {
    "rollnumber": "roll_number",
    "rollno": "roll_number",
    "fullname": "full_name",
    "name": "full_name",
    "email": "college_email",
    "collegeemail": "college_email",
    "course": "program",
    "programme": "program",
    "yearbatch": "batch",
    "batchyear": "batch",
}


class RosterImportError(Exception):
    """Raised when the uploaded roster file cannot be processed."""


def _normalise_header(value):
    text = re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())
    return HEADER_ALIASES.get(text, text)


def _read_rows(uploaded_file):
    extension = uploaded_file.name.lower().rsplit(".", 1)[-1] if "." in uploaded_file.name else ""
    uploaded_file.seek(0)

    if extension == "csv":
        try:
            decoded = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise RosterImportError("CSV must be encoded as UTF-8.") from exc
        return list(csv.reader(io.StringIO(decoded)))

    if extension == "xlsx":
        try:
            workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
            worksheet = workbook.active
            rows = list(worksheet.iter_rows(values_only=True))
            workbook.close()
            return [list(row) for row in rows]
        except Exception as exc:
            raise RosterImportError("The Excel file could not be read. Please upload a valid .xlsx file.") from exc

    raise RosterImportError("Unsupported file type. Upload a .csv or .xlsx file.")


def _cell(row, index):
    if index is None or index < 0 or index >= len(row):
        return None
    return row[index]


def import_student_roster(uploaded_file):
    """Validate a CSV/XLSX roster and insert valid new student records.

    Existing roll numbers are skipped, never overwritten. Invalid rows are
    reported individually while valid rows are imported in one transaction.
    """
    if uploaded_file.size > MAX_IMPORT_BYTES:
        raise RosterImportError("File is too large. Maximum upload size is 5 MB.")

    rows = _read_rows(uploaded_file)
    if not rows:
        raise RosterImportError("The uploaded file is empty.")

    headers = [_normalise_header(value) for value in rows[0]]
    if len(headers) != len(set(header for header in headers if header)):
        raise RosterImportError("The file contains duplicate column headings.")

    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        raise RosterImportError(
            "Missing required columns: " + ", ".join(sorted(missing))
            + ". Required headings are roll_number and full_name."
        )

    unknown = set(headers) - REQUIRED_COLUMNS - OPTIONAL_COLUMNS - {""}
    if unknown:
        raise RosterImportError(
            "Unknown columns: " + ", ".join(sorted(unknown))
            + ". Use roll_number, full_name, college_email, program, batch, cgpa and backlogs."
        )

    if len(rows) - 1 > MAX_IMPORT_ROWS:
        raise RosterImportError(f"Maximum {MAX_IMPORT_ROWS} student rows are allowed per upload.")

    positions = {name: index for index, name in enumerate(headers) if name}
    seen_roll_numbers = set()
    prepared = []
    errors = []
    blank_rows = 0

    for row_number, row in enumerate(rows[1:], start=2):
        if not any(value is not None and str(value).strip() for value in row):
            blank_rows += 1
            continue

        roll_number = str(_cell(row, positions["roll_number"]) or "").strip().upper()
        full_name = str(_cell(row, positions["full_name"]) or "").strip()
        row_errors = []

        if not roll_number:
            row_errors.append("roll_number is required")
        elif len(roll_number) > 30:
            row_errors.append("roll_number must be 30 characters or fewer")
        elif roll_number in seen_roll_numbers:
            row_errors.append("duplicate roll_number in this file")
        else:
            seen_roll_numbers.add(roll_number)

        if not full_name:
            row_errors.append("full_name is required")
        elif len(full_name) > 150:
            row_errors.append("full_name must be 150 characters or fewer")

        email = str(_cell(row, positions.get("college_email")) or "").strip()
        if email:
            try:
                validate_email(email)
            except DjangoValidationError:
                row_errors.append("college_email is not a valid email address")

        program = str(_cell(row, positions.get("program")) or "B.Tech CSE").strip() or "B.Tech CSE"
        batch = str(_cell(row, positions.get("batch")) or "").strip()

        raw_cgpa = _cell(row, positions.get("cgpa"))
        try:
            cgpa = Decimal(str(raw_cgpa).strip()) if raw_cgpa not in (None, "") else Decimal("0.00")
            if not cgpa.is_finite() or cgpa < 0 or cgpa > 10:
                row_errors.append("cgpa must be between 0 and 10")
        except (InvalidOperation, ValueError):
            cgpa = Decimal("0.00")
            row_errors.append("cgpa must be a valid number")

        raw_backlogs = _cell(row, positions.get("backlogs"))
        try:
            numeric_backlogs = Decimal(str(raw_backlogs).strip()) if raw_backlogs not in (None, "") else Decimal(0)
            if not numeric_backlogs.is_finite() or numeric_backlogs != numeric_backlogs.to_integral_value() or numeric_backlogs < 0:
                row_errors.append("backlogs must be a non-negative whole number")
                backlogs = 0
            else:
                backlogs = int(numeric_backlogs)
        except (InvalidOperation, ValueError):
            backlogs = 0
            row_errors.append("backlogs must be a non-negative whole number")

        if row_errors:
            errors.append({"row": row_number, "roll_number": roll_number, "errors": row_errors})
            continue

        prepared.append(StudentRoster(
            roll_number=roll_number,
            full_name=full_name,
            college_email=email,
            program=program,
            batch=batch,
            cgpa=cgpa,
            backlogs=backlogs,
        ))

    existing_rolls = set(
        StudentRoster.objects.filter(
            roll_number__in=[record.roll_number for record in prepared]
        ).values_list("roll_number", flat=True)
    )
    new_records = []
    skipped_existing = 0
    for record in prepared:
        if record.roll_number in existing_rolls:
            skipped_existing += 1
        else:
            new_records.append(record)

    if new_records:
        StudentRoster.objects.bulk_create(new_records, batch_size=500)

    return {
        "total_rows": max(len(rows) - 1, 0),
        "created": len(new_records),
        "skipped_existing": skipped_existing,
        "blank_rows": blank_rows,
        "error_count": len(errors),
        "errors": errors,
    }
