from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from drive.models import Drive
from .models import Application


class ApplicationPipelineTests(APITestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='pipeline_recruiter', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Acme'
        )
        self.other_recruiter = User.objects.create_user(
            username='other_recruiter', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Other Co'
        )
        self.student_a = User.objects.create_user(
            username='P001', roll_number='P001', password='StrongPass123',
            role='STUDENT', cgpa=Decimal('8.50'), backlogs=0
        )
        self.student_b = User.objects.create_user(
            username='P002', roll_number='P002', password='StrongPass123',
            role='STUDENT', cgpa=Decimal('6.50'), backlogs=1
        )
        self.drive = Drive.objects.create(
            company_name='Acme', role_title='Software Engineer', package_lpa=8,
            min_cgpa=6, max_backlogs=1, posted_by=self.recruiter
        )
        self.other_drive = Drive.objects.create(
            company_name='Other Co', role_title='Analyst', package_lpa=6,
            min_cgpa=6, max_backlogs=1, posted_by=self.other_recruiter
        )
        self.application_a = Application.objects.create(student=self.student_a, drive=self.drive)
        self.application_b = Application.objects.create(student=self.student_b, drive=self.drive)
        self.other_application = Application.objects.create(student=self.student_b, drive=self.other_drive)
        self.client.force_authenticate(self.recruiter)

    def test_recruiter_can_filter_candidates_by_academic_eligibility(self):
        response = self.client.get('/api/application/?min_cgpa=8&max_backlogs=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([item['id'] for item in results], [self.application_a.id])

    def test_recruiter_can_bulk_shortlist_own_drive_applications(self):
        response = self.client.post('/api/application/bulk-status/', {
            'application_ids': [self.application_a.id, self.application_b.id],
            'status': 'SHORTLISTED',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application_a.refresh_from_db()
        self.application_b.refresh_from_db()
        self.assertEqual(self.application_a.status, 'SHORTLISTED')
        self.assertEqual(self.application_b.status, 'SHORTLISTED')

    def test_recruiter_cannot_bulk_update_another_company_application(self):
        response = self.client.post('/api/application/bulk-status/', {
            'application_ids': [self.application_a.id, self.other_application.id],
            'status': 'SHORTLISTED',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_interview_stage_requires_a_schedule(self):
        self.application_a.status = 'SHORTLISTED'
        self.application_a.save()
        response = self.client.patch(
            f'/api/application/{self.application_a.id}/',
            {'status': 'INTERVIEW'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recruiter_can_schedule_interview_after_shortlisting(self):
        self.application_a.status = 'SHORTLISTED'
        self.application_a.save()
        response = self.client.patch(
            f'/api/application/{self.application_a.id}/',
            {
                'status': 'INTERVIEW',
                'interview_at': '2030-06-01T10:00:00Z',
                'interview_mode': 'ONLINE',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application_a.refresh_from_db()
        self.assertEqual(self.application_a.status, 'INTERVIEW')
        self.assertEqual(self.application_a.interview_mode, 'ONLINE')

    def test_terminal_application_status_cannot_be_reopened(self):
        self.application_a.status = 'SELECTED'
        self.application_a.save()
        response = self.client.patch(
            f'/api/application/{self.application_a.id}/',
            {'status': 'SHORTLISTED'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
