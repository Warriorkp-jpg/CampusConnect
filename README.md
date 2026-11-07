# CampusConnect — JMIT Placement Management Portal

CampusConnect is a single-college placement portal for JMIT, built with Django, Django REST Framework, SimpleJWT and a Bootstrap/Vanilla JavaScript frontend.

## Roles
- **Student:** registers with a college roll number present in the TPO-maintained roster, signs in with roll number and password, views active drives, applies when eligible and tracks application decisions.
- **Recruiter:** registers with company details. New accounts are PENDING; a TPO must approve them before they can publish drives or review applicants. Recruiters can only access applications for their own drives.
- **TPO:** manages the student roster, approves/rejects recruiters, monitors all drives and applications, and has placement-wide visibility.

TPO accounts are created by a trusted administrator using Django admin or createsuperuser followed by assigning the TPO role. There is no public TPO registration endpoint.

## Features
- JWT login; student username is set to their verified roll number.
- College roster verification prevents arbitrary roll-number registration. The roster must be populated by the TPO before students can register.
- Server-assigned roles; public registration cannot choose a role.
- Recruiter approval workflow.
- Drive creation, editing and deletion by approved recruiters (own drives) or TPO.
- CGPA/backlog eligibility checks and duplicate application protection.
- Application progression: APPLIED -> SHORTLISTED -> SELECTED or REJECTED.
- Queryset-level isolation for student and recruiter application visibility.
- TPO dashboard, roster management and recruiter review endpoints.
- Environment-based secret key, debug setting, allowed hosts and CORS origins.

## Tech stack
- Python 3.11+ (use a Python version supported by the installed Django release)
- Django / Django REST Framework / SimpleJWT
- SQLite for local development
- Bootstrap 5 and vanilla JavaScript

## Setup
1. Clone the repository and enter the project folder.
2. Create and activate a virtual environment.
3. Install dependencies: pip install -r requirements.txt
4. Set environment variables. At minimum, set a strong DJANGO_SECRET_KEY for any shared/deployed environment. The settings module reads environment variables directly; it does not load a .env file automatically.
5. Back up any existing db.sqlite3, then run:
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
6. Sign in to /admin/. Assign a trusted account the application role TPO (the Django superuser flag is separate from the CampusConnect role).
7. In the TPO portal, add student roll numbers to the student roster. Students can then register with those roll numbers.
8. Recruiters register through the portal and wait for TPO approval.

Open index.html using a local static server such as VS Code Live Server at http://127.0.0.1:5500. Set the frontend API base URL to your backend URL if it differs from http://127.0.0.1:8000.

## API overview
| Endpoint | Access | Purpose |
|---|---|---|
| POST /api/register/student/ | Public | Student registration; requires roster roll number |
| POST /api/register/recruiter/ | Public | Recruiter registration; status becomes PENDING |
| POST /api/login/ | Public | JWT login; student username is their roll number |
| GET /api/me/ | Authenticated | Current account profile and role |
| GET /api/student-zone/ | Student | Student dashboard |
| GET /api/recruiter-zone/ | Recruiter | Recruiter dashboard and approval status |
| GET /api/tpo-zone/ | TPO | Placement overview counts |
| GET /api/tpo/recruiters/pending/ | TPO | Pending recruiter approvals |
| PATCH /api/tpo/recruiters/{id}/review/ | TPO | Set recruiter status to APPROVED or REJECTED |
| /api/tpo/student-roster/ | TPO | List/add/delete eligible student roster entries |
| /api/drive/ | Authenticated | List/retrieve drives; approved recruiters manage own drives; TPO manages all |
| /api/application/ | Authenticated | Students create/view own applications; recruiters view/review own-drive applicants; TPO views all |

## Important notes
- A roll number alone is not proof of enrollment. Student registration succeeds only if the TPO has first entered that roll number in the roster.
- Student registration currently accepts CGPA and backlog values from the student. For production use, import academic values from an authoritative college record rather than trusting self-reported values.
- The portal stores JWTs in browser session storage. Use HTTPS in deployment and never expose tokens in logs or screenshots.
- Configure a production database, HTTPS, secure settings, trusted CORS origins, secret management and backups before public launch.
- Run automated tests with python manage.py test.
