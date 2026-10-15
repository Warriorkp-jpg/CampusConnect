# 🎓 CampusConnect — Placement Management REST API

**CampusConnect** is a decoupled, role-based Placement Management System built using **Python, Django, Django REST Framework (DRF), SimpleJWT, and Bootstrap 5**. 

Designed with an API-first architecture, it digitizes the campus recruitment lifecycle by automating student academic eligibility validation (CGPA and active backlogs) and enforcing strict Role-Based Access Control (RBAC) across **Admin**, **Recruiter**, and **Student** accounts.

---

## 🚀 Key Features

* **Stateless JWT Authentication (`accounts`):** Custom user model (`AbstractUser`) integrated with `SimpleJWT` for secure Access & Refresh token generation and password hashing.
* **Role-Based Access Control (RBAC):** Custom DRF permission classes (`IsAdminRole`, `IsRecruiterRole`, `IsStudentRole`) and dynamic action-level permission routing via `get_permissions()`.
* **Company Drive Management (`drive`):** Full CRUD functionality using `ModelViewSet` and `DefaultRouter`. Optimized with `select_related('posted_by')` to eliminate N+1 query overhead.
* **Automated Academic Eligibility Engine (`application`):** Serializer-level business validation (`validate()`) that intercepts job applications in real time to verify:
  * Student CGPA meets or exceeds `drive.min_cgpa`.
  * Student active backlogs do not exceed `drive.max_backlogs`.
  * Duplicate application prevention at both the Serializer and Database Schema levels (`unique_together`).
* **Strict Data Isolation:** Overridden `get_queryset()` ensures students can only view their own applications while recruiters and admins can oversee all submissions.
* **Interactive Client Portal (`campusconnect_frontend_portal.html`):** Responsive Bootstrap 5 frontend utilizing the JavaScript `fetch()` API, `Authorization: Bearer` headers, and CORS middleware.

---

## 🛠️ Tech Stack

* **Backend:** Python 3, Django, Django REST Framework (DRF)
* **Authentication & Security:** `djangorestframework-simplejwt` (JWT), `django-cors-headers`
* **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript (Fetch API)
* **Database:** SQLite3 (Development) / MySQL 8 Ready
* **API Testing:** Postman & Interactive Frontend Inspector

---

## 📂 Project Architecture

```text
CampusConnect/
├── accounts/                        # Identity, Custom User Model & RBAC
│   ├── models.py                    # Custom User (role, cgpa, backlogs)
│   ├── serializers.py               # RegisterSerializer with create_user() hashing
│   ├── permissions.py               # IsAdminRole, IsRecruiterRole, IsStudentRole
│   └── views.py                     # Registration & Role-Protected Views
├── drive/                           # Company Job Drives Module
│   ├── models.py                    # Drive schema (package_lpa, min_cgpa, max_backlogs)
│   ├── serializers.py               # DriveSerializer with read-only posted_by
│   └── views.py                     # DriveViewSet with action-based permissions
├── application/                     # Student Application & Validation Engine
│   ├── models.py                    # Application junction table (unique_together)
│   ├── serializers.py               # ApplicationSerializer with CGPA/Backlog validate()
│   └── views.py                     # ApplicationViewSet with isolated get_queryset()
├── rbac_project/                    # Core Project Configuration
│   ├── settings.py                  # AUTH_USER_MODEL, JWT, CORS & Installed Apps
│   └── urls.py                      # Central routing & DRF DefaultRouter
├── campusconnect_frontend_portal.html # Bootstrap 5 Frontend Client
└── requirements.txt                 # Project Dependencies