from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import StudentRoster
from .serializers import (
    StudentRegisterSerializer, RecruiterRegisterSerializer, UserProfileSerializer,
    StudentRosterSerializer, RecruiterReviewSerializer
)
from .permissions import IsStudentRole, IsRecruiterRole, IsTPORole

User = get_user_model()


class StudentRegisterView(generics.CreateAPIView):
    serializer_class = StudentRegisterSerializer
    permission_classes = [AllowAny]


class RecruiterRegisterView(generics.CreateAPIView):
    serializer_class = RecruiterRegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class StudentDashboardView(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response({
            'message': f'Welcome {request.user.username}',
            'role': request.user.role,
            'profile': UserProfileSerializer(request.user).data,
            'access': 'View eligible drives, apply, and track your applications.'
        })


class RecruiterDashboardView(APIView):
    permission_classes = [IsRecruiterRole]

    def get(self, request):
        return Response({
            'message': f'Welcome {request.user.company_name or request.user.username}',
            'role': request.user.role,
            'approval_status': request.user.recruiter_status,
            'access': 'Drive management is enabled after TPO approval.'
        })


class TPODashboardView(APIView):
    permission_classes = [IsTPORole]

    def get(self, request):
        return Response({
            'message': 'Welcome to the TPO dashboard',
            'role': 'TPO',
            'pending_recruiters': User.objects.filter(
                role='RECRUITER', recruiter_status='PENDING'
            ).count(),
            'registered_students': User.objects.filter(role='STUDENT').count(),
            'roster_students': StudentRoster.objects.count(),
        })


class RecruiterApprovalView(generics.UpdateAPIView):
    queryset = User.objects.filter(role='RECRUITER')
    serializer_class = RecruiterReviewSerializer
    permission_classes = [IsTPORole]
    http_method_names = ['patch', 'options', 'head']


class PendingRecruitersView(generics.ListAPIView):
    serializer_class = RecruiterReviewSerializer
    permission_classes = [IsTPORole]

    def get_queryset(self):
        return User.objects.filter(
            role='RECRUITER', recruiter_status='PENDING'
        ).order_by('date_joined')


class StudentRosterViewSet(viewsets.ModelViewSet):
    queryset = StudentRoster.objects.all().order_by('roll_number')
    serializer_class = StudentRosterSerializer
    permission_classes = [IsTPORole]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    @action(detail=False, methods=['get'], url_path='unregistered')
    def unregistered(self, request):
        records = self.get_queryset().filter(student_user__isnull=True)
        page = self.paginate_queryset(records)
        serializer = self.get_serializer(page or records, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
