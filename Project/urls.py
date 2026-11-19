from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.serializers import CampusConnectTokenObtainPairSerializer
from accounts.views import (
    StudentRegisterView, StudentOTPRequestView, StudentOTPVerifyView, RecruiterRegisterView, MeView,
    StudentProfileView, StudentResumeDownloadView, NotificationViewSet, TPOApplicationExportView,
    StudentDashboardView, RecruiterDashboardView, TPODashboardView,
    PendingRecruitersView, RecruiterApprovalView, StudentRosterViewSet, StudentRosterImportView,
)
from drive.views import DriveViewSet
from application.views import ApplicationViewSet


class CampusConnectTokenObtainPairView(TokenObtainPairView):
    serializer_class = CampusConnectTokenObtainPairSerializer


router = DefaultRouter()
router.register(r'drive', DriveViewSet, basename='drive')
router.register(r'application', ApplicationViewSet, basename='application')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'tpo/student-roster', StudentRosterViewSet, basename='student-roster')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),

    path('api/register/student/request-otp/', StudentOTPRequestView.as_view(), name='student_otp_request'),
    path('api/register/student/verify-otp/', StudentOTPVerifyView.as_view(), name='student_otp_verify'),
    path('api/register/student/', StudentRegisterView.as_view(), name='student_register'),
    path('api/register/recruiter/', RecruiterRegisterView.as_view(), name='recruiter_register'),
    path('api/login/', CampusConnectTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/me/', MeView.as_view(), name='me'),
    path('api/student-profile/', StudentProfileView.as_view(), name='student_profile'),
    path('api/students/<int:student_id>/resume/', StudentResumeDownloadView.as_view(), name='student_resume_download'),

    path('api/student-zone/', StudentDashboardView.as_view(), name='student_zone'),
    path('api/recruiter-zone/', RecruiterDashboardView.as_view(), name='recruiter_zone'),
    path('api/tpo-zone/', TPODashboardView.as_view(), name='tpo_zone'),

    path('api/tpo/recruiters/pending/', PendingRecruitersView.as_view(), name='pending_recruiters'),
    path('api/tpo/student-roster/import/', StudentRosterImportView.as_view(), name='student_roster_import'),
    path('api/tpo/reports/applications.csv/', TPOApplicationExportView.as_view(), name='tpo_application_export'),
    path('api/tpo/recruiters/<int:pk>/review/', RecruiterApprovalView.as_view(), name='review_recruiter'),

    path('api/', include(router.urls)),
]
