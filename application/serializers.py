from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    STATUS_TRANSITIONS = {
        'APPLIED': {'SHORTLISTED', 'REJECTED'},
        'SHORTLISTED': {'SELECTED', 'REJECTED'},
        'SELECTED': set(),
        'REJECTED': set(),
    }

    # Read-only fields so the student only has to send {"drive": 1} in Postman!
    student_name = serializers.ReadOnlyField(source='student.username')
    company_name = serializers.ReadOnlyField(source='drive.company_name')
    role_title = serializers.ReadOnlyField(source='drive.role_title')

    class Meta:
        model = Application
        fields = [
            'id',
            'student',
            'student_name',
            'drive',
            'company_name',
            'role_title',
            'status',
            'applied_at',
        ]
        # The student cannot fake their own ID or manually set status to 'SELECTED'!
        read_only_fields = ['student', 'applied_at']

    def validate(self, data):
        # Status-only PATCH requests from recruiters/admins must not rerun
        # application eligibility checks or require the drive field.
        if self.instance is not None:
            next_status = data.get('status')
            if next_status and next_status != self.instance.status:
                allowed_statuses = self.STATUS_TRANSITIONS[self.instance.status]
                if next_status not in allowed_statuses:
                    allowed_text = ', '.join(sorted(allowed_statuses)) or 'no further changes'
                    raise serializers.ValidationError({
                        'status': (
                            f"Cannot change an application from {self.instance.status} "
                            f"to {next_status}. Allowed next status: {allowed_text}."
                        )
                    })
            return data

        # 1. Grab the logged-in student from the request context
        student = self.context['request'].user
        drive = data['drive']

        # 2. Check Duplicate Application
        if Application.objects.filter(student=student, drive=drive).exists():
            raise serializers.ValidationError(
                "You have already applied for this placement drive."
            )

        # 3. Check CGPA Eligibility
        if student.cgpa < drive.min_cgpa:
            raise serializers.ValidationError(
                f"Not Eligible: Your CGPA ({student.cgpa}) is less than the required CGPA ({drive.min_cgpa})."
            )

        # 4. Check Active Backlogs Eligibility
        if student.backlogs > drive.max_backlogs:
            raise serializers.ValidationError(
                f"Not Eligible: You have {student.backlogs} backlogs, but the maximum allowed is {drive.max_backlogs}."
            )

        return data

    def get_fields(self):
        fields = super().get_fields()
        # The student creates an APPLIED record only; reviewer decisions are
        # writable on updates, where the viewset enforces recruiter/admin role.
        if self.instance is None:
            fields['status'].read_only = True
        return fields
