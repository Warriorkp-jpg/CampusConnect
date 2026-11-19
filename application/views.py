from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsStudentRole, IsApprovedRecruiter, IsTPORole
from accounts.notifications import notify_user
from .models import Application
from .serializers import ApplicationSerializer


class IsApplicationReviewer(IsApprovedRecruiter):
    def has_permission(self, request, view):
        return super().has_permission(request, view) or IsTPORole().has_permission(request, view)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        user = self.request.user
        base = Application.objects.select_related(
            'student', 'student__student_profile', 'drive', 'drive__posted_by'
        ).order_by('-applied_at')
        if not user.is_authenticated:
            return Application.objects.none()
        if user.role == 'STUDENT':
            queryset = base.filter(student=user)
        elif user.role == 'TPO':
            queryset = base
        elif user.role == 'RECRUITER' and user.recruiter_status == 'APPROVED':
            queryset = base.filter(drive__posted_by=user)
        else:
            return Application.objects.none()

        params = self.request.query_params
        status_value = params.get('status')
        valid_statuses = {choice[0] for choice in Application.STATUS_CHOICES}
        if status_value:
            if status_value not in valid_statuses:
                raise ValidationError({'status': 'Unknown application status.'})
            queryset = queryset.filter(status=status_value)

        drive_id = params.get('drive')
        if drive_id:
            if not drive_id.isdigit():
                raise ValidationError({'drive': 'Drive must be a valid numeric ID.'})
            queryset = queryset.filter(drive_id=int(drive_id))

        for parameter, lookup in (
            ('min_cgpa', 'student__cgpa__gte'),
            ('max_cgpa', 'student__cgpa__lte'),
        ):
            raw_value = params.get(parameter)
            if raw_value:
                try:
                    value = Decimal(raw_value)
                except InvalidOperation:
                    raise ValidationError({parameter: 'Enter a valid number.'})
                if value < 0 or value > 10:
                    raise ValidationError({parameter: 'CGPA must be between 0 and 10.'})
                queryset = queryset.filter(**{lookup: value})

        max_backlogs = params.get('max_backlogs')
        if max_backlogs:
            if not max_backlogs.isdigit():
                raise ValidationError({'max_backlogs': 'Enter a non-negative whole number.'})
            queryset = queryset.filter(student__backlogs__lte=int(max_backlogs))

        search = params.get('search', '').strip()[:100]
        if search:
            queryset = queryset.filter(
                Q(student__roll_number__icontains=search)
                | Q(student__first_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(drive__company_name__icontains=search)
                | Q(drive__role_title__icontains=search)
            )
        return queryset

    def get_permissions(self):
        if self.action == 'create':
            return [IsStudentRole()]
        if self.action in ('update', 'partial_update', 'bulk_status'):
            return [IsApplicationReviewer()]
        if self.action == 'destroy':
            return [IsTPORole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                application = serializer.save(student=self.request.user)
                recruiter = application.drive.posted_by
                transaction.on_commit(lambda: notify_user(
                    recruiter,
                    'New placement application',
                    f'{application.student.get_full_name() or application.student.roll_number} applied for {application.drive.role_title}.',
                    'APPLICATION',
                ))
        except IntegrityError:
            raise ValidationError({'drive': 'You have already applied to this placement drive.'})

    def perform_update(self, serializer):
        if self.request.user.role == 'RECRUITER':
            if serializer.instance.drive.posted_by_id != self.request.user.id:
                raise PermissionDenied('You can only review applications to your own drives.')
        previous_status = serializer.instance.status
        application = serializer.save()
        if application.status != previous_status:
            transaction.on_commit(lambda: notify_user(
                application.student,
                'Application status updated',
                f'Your application for {application.drive.role_title} is now {application.status.lower()}.',
                'APPLICATION',
            ))

    @action(detail=False, methods=['post'], url_path='bulk-status')
    def bulk_status(self, request):
        application_ids = request.data.get('application_ids')
        next_status = request.data.get('status')
        if not isinstance(application_ids, list) or not application_ids or len(application_ids) > 100:
            raise ValidationError({'application_ids': 'Provide between 1 and 100 application IDs.'})
        if not all(isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in application_ids):
            raise ValidationError({'application_ids': 'Every application ID must be a positive integer.'})
        if len(set(application_ids)) != len(application_ids):
            raise ValidationError({'application_ids': 'Duplicate application IDs are not allowed.'})
        valid_statuses = {choice[0] for choice in Application.STATUS_CHOICES}
        if next_status not in valid_statuses:
            raise ValidationError({'status': 'Choose a valid application status.'})

        applications = list(self.get_queryset().filter(id__in=application_ids))
        if len(applications) != len(application_ids):
            raise ValidationError({'application_ids': 'One or more applications were not found or are outside your access.'})

        update_data = {'status': next_status}
        if next_status == 'INTERVIEW':
            update_data['interview_at'] = request.data.get('interview_at')
            update_data['interview_mode'] = request.data.get('interview_mode', '')

        serializers = []
        for application in applications:
            item = self.get_serializer(application, data=update_data, partial=True)
            item.is_valid(raise_exception=True)
            serializers.append(item)

        previous_statuses = {item.instance.id: item.instance.status for item in serializers}
        with transaction.atomic():
            updated = [item.save() for item in serializers]
            for application in updated:
                if application.status != previous_statuses[application.id]:
                    transaction.on_commit(lambda app=application: notify_user(
                        app.student,
                        'Application status updated',
                        f'Your application for {app.drive.role_title} is now {app.status.lower()}.',
                        'APPLICATION',
                    ))
        return Response(self.get_serializer(updated, many=True).data, status=status.HTTP_200_OK)
