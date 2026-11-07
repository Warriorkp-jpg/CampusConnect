from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers import CampusConnectTokenObtainPairSerializer
from accounts.views import (
    StudentRegisterView, RecruiterRegisterView, MeView,
    StudentDashboardView, RecruiterDashboardView, TPODashboardView,
    PendingRecruitersView, RecruiterApprovalView, StudentRosterViewSet,
)
from drive.views import DriveViewSet
from application.views import ApplicationViewSet


class CampusConnectTokenObtainPairView(TokenObtainPairView):
    serializer_class = CampusConnectTokenObtainPairSerializer


router = DefaultRouter()
router.register(r'drive', DriveViewSet, basename='drive')
router.register(r'application', ApplicationViewSet, basename='application')
router.register(r'tpo/student-roster', StudentRosterViewSet, basename='student-roster')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/student/', StudentRegisterView.as_view(), name='student_register'),
    path('api/register/recruiter/', RecruiterRegisterView.as_view(), name='recruiter_register'),
    path('api/login/', CampusConnectTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/me/', MeView.as_view(), name='me'),

    path('api/student-zone/', StudentDashboardView.as_view(), name='student_zone'),
    path('api/recruiter-zone/', RecruiterDashboardView.as_view(), name='recruiter_zone'),
    path('api/tpo-zone/', TPODashboardView.as_view(), name='tpo_zone'),

    path('api/tpo/recruiters/pending/', PendingRecruitersView.as_view(), name='pending_recruiters'),
    path('api/tpo/recruiters/<int:pk>/review/', RecruiterApprovalView.as_view(), name='review_recruiter'),

    path('api/', include(router.urls)),
]
