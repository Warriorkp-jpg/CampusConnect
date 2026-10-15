from django.shortcuts import render
from .serializers import RegisterSerializer
from .permissions import IsAdminRole ,IsRecruiterRole ,IsStudentRole
from rest_framework import viewsets,generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth import get_user_model
# Create your views here.

User = get_user_model()

# 1. Public Endpoint: Anyone can register
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class StudentDashboardView(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response({
            "message": f"Welcome Student {request.user.username}!",
            "role": request.user.role,
            "access": "You can view drives and apply for jobs."
        })


class RecruiterDashboardView(APIView):
    permission_classes = [IsRecruiterRole]

    def get(self, request):
        return Response({
            "message": f"Welcome Recruiter {request.user.username}!",
            "role": request.user.role,
            "access": "You can post new placement drives and shortlist students."
        })

class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({
            "message": f"Welcome Admin {request.user.username}!",
            "role": request.user.role,
            "access": "You have full control over CampusConnect."
        })  


# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer

#     def get_permissions(self):
#         # 1. Anyone can register (POST /api/users/)
#         if self.action == 'create':
#             return [AllowAny()]
        
#         # 2. Only ADMIN can delete a user or see the full list of all users
#         elif self.action in ['list', 'destroy']:
#             return [IsAdminRole()]
        
#         # 3. Any logged-in user can view/update details
#         return [IsAuthenticated()]