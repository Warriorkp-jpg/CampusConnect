from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import (
    RegisterView,
    StudentDashboardView,
    RecruiterDashboardView,
    AdminDashboardView,
)
from drive.views import DriveViewSet
from application.views import ApplicationViewSet  

# Create a router and register ViewSets
router = DefaultRouter()
router.register(r'drive', DriveViewSet, basename='drive')
router.register(r'application', ApplicationViewSet, basename='application')  # <-- 2. Add this!

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/student-zone/', StudentDashboardView.as_view(), name='student_zone'),
    path('api/recruiter-zone/', RecruiterDashboardView.as_view(), name='recruiter_zone'),
    path('api/admin-zone/', AdminDashboardView.as_view(), name='admin_zone'),

    
    path('api/', include(router.urls)),
]