from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Application
from .serializers import ApplicationSerializer
from accounts.permissions import IsStudentRole, IsRecruiterRole


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer

    # 1. Data Isolation: Students only see their own applications!
    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.select_related('student', 'drive').all()
        
        if user.role == 'STUDENT':
            return queryset.filter(student=user)
        return queryset

    # 2. Role Permissions: ONLY Students can apply (create)
    def get_permissions(self):
        if self.action == 'create':
            return [IsStudentRole()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsRecruiterRole()]
        return [IsAuthenticated()]

    # 3. Automatically attach the logged-in Student when saving
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)