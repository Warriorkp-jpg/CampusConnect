from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsApprovedRecruiter, IsTPORole
from .models import Drive
from .serializers import DriveSerializer


class DriveViewSet(viewsets.ModelViewSet):
    serializer_class = DriveSerializer

    def get_queryset(self):
        user = self.request.user
        base = Drive.objects.select_related('posted_by').all().order_by('-created_at')
        if not user.is_authenticated:
            return Drive.objects.none()
        if user.role == 'TPO':
            return base
        if user.role == 'RECRUITER':
            return base.filter(posted_by=user)
        if user.role == 'STUDENT':
            return base.filter(
                is_active=True, posted_by__role='RECRUITER',
                posted_by__recruiter_status='APPROVED'
            )
        return Drive.objects.none()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            # TPO can manage any drive; approved recruiters can manage their own.
            return [IsApprovedRecruiterOrTPO()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


from rest_framework.permissions import BasePermission


class IsApprovedRecruiterOrTPO(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (
                user.role == 'TPO' or (
                    user.role == 'RECRUITER' and user.recruiter_status == 'APPROVED'
                )
            )
        )

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'TPO' or obj.posted_by_id == request.user.id
