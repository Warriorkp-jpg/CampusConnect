from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from accounts.permissions import IsStudentRole, IsApprovedRecruiter, IsTPORole
from .models import Application
from .serializers import ApplicationSerializer


class IsApplicationReviewer(IsApprovedRecruiter):
    def has_permission(self, request, view):
        return super().has_permission(request, view) or IsTPORole().has_permission(request, view)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        user = self.request.user
        base = Application.objects.select_related('student', 'drive', 'drive__posted_by')
        if not user.is_authenticated:
            return Application.objects.none()
        if user.role == 'STUDENT':
            return base.filter(student=user)
        if user.role == 'TPO':
            return base
        if user.role == 'RECRUITER' and user.recruiter_status == 'APPROVED':
            return base.filter(drive__posted_by=user)
        return Application.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [IsStudentRole()]
        if self.action in ('update', 'partial_update'):
            return [IsApplicationReviewer()]
        if self.action == 'destroy':
            return [IsTPORole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role == 'RECRUITER':
            if serializer.instance.drive.posted_by_id != self.request.user.id:
                raise PermissionDenied('You can only review applications to your own drives.')
        serializer.save()
