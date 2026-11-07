from rest_framework.permissions import BasePermission


class IsRole(BasePermission):
    role = None

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == self.role
        )


class IsTPORole(IsRole):
    role = 'TPO'


class IsAdminRole(IsTPORole):
    """Backward-compatible alias; application role is now TPO."""


class IsRecruiterRole(IsRole):
    role = 'RECRUITER'


class IsApprovedRecruiter(IsRecruiterRole):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.recruiter_status == 'APPROVED'


class IsStudentRole(IsRole):
    role = 'STUDENT'
