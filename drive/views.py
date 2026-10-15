from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Drive
from .serializers import DriveSerializer
from accounts.permissions import IsRecruiterRole


class DriveViewSet(viewsets.ModelViewSet):
    queryset = Drive.objects.select_related('posted_by').all().order_by('-created_at')
    serializer_class = DriveSerializer

    # 1. Dynamic Role-Based Permissions per action
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Any logged-in user (Student, Recruiter, Admin) can VIEW drives
            return [IsAuthenticated()]
        # ONLY Recruiters can create, update, or delete drives
        return [IsRecruiterRole()]

    # 2. Automatically attach the logged-in Recruiter as 'posted_by'
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)