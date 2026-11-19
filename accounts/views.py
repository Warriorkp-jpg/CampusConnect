from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from datetime import timedelta
import secrets
import uuid
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import StudentRoster, StudentEmailOTP, StudentProfile
from .roster_import import import_student_roster, RosterImportError
from .serializers import (
    StudentOTPRequestSerializer, StudentOTPVerifySerializer, StudentRegistrationCompleteSerializer,
    RecruiterRegisterSerializer, UserProfileSerializer, StudentProfileSerializer,
    StudentRosterSerializer, RecruiterReviewSerializer
)
from .permissions import IsStudentRole, IsRecruiterRole, IsTPORole
from application.models import Application

User = get_user_model()


OTP_LENGTH = 6
OTP_LIFETIME_MINUTES = 10
OTP_RESEND_SECONDS = 60
OTP_MAX_REQUESTS_PER_HOUR = 5
OTP_MAX_VERIFY_ATTEMPTS = 5


class StudentOTPRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'student_otp'

    def post(self, request):
        serializer = StudentOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roll_number = serializer.validated_data['roll_number']
        now = timezone.now()
        StudentEmailOTP.objects.filter(expires_at__lt=now - timedelta(days=1)).delete()
        response_challenge = uuid.uuid4()

        record = StudentRoster.objects.filter(
            roll_number__iexact=roll_number,
            student_user__isnull=True,
        ).first()

        if record and record.college_email:
            recent = StudentEmailOTP.objects.filter(
                roll_number__iexact=record.roll_number,
                created_at__gte=now - timedelta(hours=1),
                consumed_at__isnull=True,
            )
            latest = recent.order_by('-created_at').first()
            allowed = recent.count() < OTP_MAX_REQUESTS_PER_HOUR
            if latest and (now - latest.created_at).total_seconds() < OTP_RESEND_SECONDS:
                allowed = False

            if allowed:
                code = f'{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}'
                challenge = StudentEmailOTP.objects.create(
                    roll_number=record.roll_number,
                    code_hash=make_password(code),
                    expires_at=now + timedelta(minutes=OTP_LIFETIME_MINUTES),
                )
                subject = 'Your CampusConnect student verification code'
                message = (
                    f'Hello {record.full_name},\n\n'
                    f'Your CampusConnect verification code is {code}. '
                    f'It expires in {OTP_LIFETIME_MINUTES} minutes.\n\n'
                    'If you did not request this code, you can ignore this email.'
                )
                try:
                    sent = send_mail(
                        subject, message, settings.DEFAULT_FROM_EMAIL,
                        [record.college_email], fail_silently=False,
                    )
                    if sent != 1:
                        challenge.delete()
                    else:
                        response_challenge = challenge.challenge_id
                except Exception:
                    challenge.delete()

        return Response({
            'detail': 'If the roll number is eligible, a verification code has been sent to the college email on the roster.',
            'challenge_id': str(response_challenge),
        }, status=status.HTTP_200_OK)


class StudentOTPVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'student_otp_verify'

    def post(self, request):
        serializer = StudentOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        challenge = StudentEmailOTP.objects.filter(
            challenge_id=serializer.validated_data['challenge_id'],
            consumed_at__isnull=True,
        ).first()
        now = timezone.now()

        if (
            not challenge or challenge.expires_at <= now
            or challenge.verified_at is not None
            or challenge.attempts >= OTP_MAX_VERIFY_ATTEMPTS
        ):
            return Response({'detail': 'The verification code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        challenge.attempts += 1
        if not check_password(serializer.validated_data['otp'], challenge.code_hash):
            challenge.save(update_fields=['attempts'])
            return Response({'detail': 'The verification code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        challenge.verified_at = now
        challenge.save(update_fields=['attempts', 'verified_at'])
        return Response({'detail': 'Email verified. Complete your student registration.'})


class StudentRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegistrationCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        now = timezone.now()

        try:
            with transaction.atomic():
                challenge = StudentEmailOTP.objects.select_for_update().get(
                    challenge_id=serializer.validated_data['challenge_id'],
                    consumed_at__isnull=True,
                    verified_at__isnull=False,
                    expires_at__gt=now,
                )
                record = StudentRoster.objects.select_for_update().get(
                    roll_number__iexact=challenge.roll_number,
                    student_user__isnull=True,
                )
                full_name_parts = record.full_name.split(maxsplit=1)
                user = User.objects.create_user(
                    username=record.roll_number,
                    roll_number=record.roll_number,
                    email=record.college_email,
                    first_name=full_name_parts[0] if full_name_parts else '',
                    last_name=full_name_parts[1] if len(full_name_parts) > 1 else '',
                    password=serializer.validated_data['password'],
                    role='STUDENT',
                    cgpa=record.cgpa,
                    backlogs=record.backlogs,
                )
                record.student_user = user
                record.save(update_fields=['student_user'])
                challenge.consumed_at = now
                challenge.save(update_fields=['consumed_at'])
        except (StudentEmailOTP.DoesNotExist, StudentRoster.DoesNotExist):
            return Response(
                {'detail': 'Verification is incomplete, expired, or this roll number is already registered.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {'detail': 'This student account has already been registered.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)


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
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def perform_destroy(self, instance):
        if instance.student_user_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('A registered student roster record cannot be deleted.')
        instance.delete()

    def perform_update(self, serializer):
        record = serializer.save()
        if record.student_user_id:
            student = record.student_user
            student.cgpa = record.cgpa
            student.backlogs = record.backlogs
            student.email = record.college_email or student.email
            student.save(update_fields=['cgpa', 'backlogs', 'email'])

    @action(detail=False, methods=['get'], url_path='unregistered')
    def unregistered(self, request):
        records = self.get_queryset().filter(student_user__isnull=True)
        page = self.paginate_queryset(records)
        serializer = self.get_serializer(page if page is not None else records, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)



class StudentRosterImportView(APIView):
    """Bulk-import official student records from a CSV or XLSX upload."""
    permission_classes = [IsTPORole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'detail': 'Upload a CSV or XLSX file using the file field.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            result = import_student_roster(uploaded_file)
        except RosterImportError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)



class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsStudentRole]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile


class StudentResumeDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        profile = get_object_or_404(StudentProfile, user_id=student_id)
        user = request.user
        allowed = user.role == 'TPO' or (
            user.role == 'STUDENT' and user.id == student_id
        )
        if user.role == 'RECRUITER' and user.recruiter_status == 'APPROVED':
            allowed = Application.objects.filter(
                student_id=student_id,
                drive__posted_by=user,
            ).exists()
        if not allowed or not profile.resume:
            raise Http404
        filename = f'{profile.user.roll_number or profile.user.username}_resume.pdf'
        return FileResponse(
            profile.resume.open('rb'),
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )
