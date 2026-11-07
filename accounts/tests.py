from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User, StudentRoster
from drive.models import Drive
from application.models import Application


class RegistrationWorkflowTests(APITestCase):
    def test_student_registration_requires_roster_and_uses_roster_academics(self):
        missing = self.client.post('/api/register/student/', {
            'roll_number': 'JMIT001', 'password': 'StrongPass123'
        }, format='json')
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)

        record = StudentRoster.objects.create(
            roll_number='JMIT001', full_name='Test Student',
            cgpa=Decimal('8.25'), backlogs=0
        )
        response = self.client.post('/api/register/student/', {
            'roll_number': 'jmit001', 'email': 'student@example.com',
            'password': 'StrongPass123', 'role': 'TPO', 'cgpa': 10, 'backlogs': 0,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(roll_number='JMIT001')
        self.assertEqual(user.role, 'STUDENT')
        self.assertEqual(user.cgpa, record.cgpa)
        self.assertEqual(user.backlogs, record.backlogs)
        self.assertEqual(record.student_user_id, user.id)

    def test_recruiter_registration_is_pending_and_role_is_server_assigned(self):
        response = self.client.post('/api/register/recruiter/', {
            'username': 'acme_hr', 'email': 'hr@acme.example',
            'password': 'StrongPass123', 'company_name': 'Acme', 'role': 'TPO',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recruiter = User.objects.get(username='acme_hr')
        self.assertEqual(recruiter.role, 'RECRUITER')
        self.assertEqual(recruiter.recruiter_status, 'PENDING')


class RoleIsolationTests(APITestCase):
    def setUp(self):
        self.student_a = User.objects.create_user(
            username='S001', roll_number='S001', password='StrongPass123',
            role='STUDENT', cgpa=8, backlogs=0
        )
        self.student_b = User.objects.create_user(
            username='S002', roll_number='S002', password='StrongPass123',
            role='STUDENT', cgpa=8, backlogs=0
        )
        self.recruiter_a = User.objects.create_user(
            username='recruiter_a', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Acme'
        )
        self.recruiter_b = User.objects.create_user(
            username='recruiter_b', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Beta'
        )
        self.tpo = User.objects.create_user(
            username='tpo', password='StrongPass123', role='TPO'
        )
        self.drive_a = Drive.objects.create(
            company_name='Acme', role_title='Developer', package_lpa=5,
            min_cgpa=6, max_backlogs=0, posted_by=self.recruiter_a
        )
        self.drive_b = Drive.objects.create(
            company_name='Beta', role_title='Analyst', package_lpa=6,
            min_cgpa=6, max_backlogs=0, posted_by=self.recruiter_b
        )
        self.app_a = Application.objects.create(student=self.student_a, drive=self.drive_a)
        self.app_b = Application.objects.create(student=self.student_b, drive=self.drive_b)

    def test_student_only_sees_own_applications(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get('/api/application/')
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([item['id'] for item in results], [self.app_a.id])

    def test_recruiter_only_sees_applications_for_own_drives(self):
        self.client.force_authenticate(self.recruiter_a)
        response = self.client.get('/api/application/')
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([item['id'] for item in results], [self.app_a.id])

    def test_tpo_sees_all_applications(self):
        self.client.force_authenticate(self.tpo)
        response = self.client.get('/api/application/')
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual({item['id'] for item in results}, {self.app_a.id, self.app_b.id})

    def test_pending_recruiter_cannot_publish_drive(self):
        pending = User.objects.create_user(
            username='pending', password='StrongPass123',
            role='RECRUITER', recruiter_status='PENDING', company_name='Pending Co'
        )
        self.client.force_authenticate(pending)
        response = self.client.post('/api/drive/', {
            'company_name': 'Impersonated Co', 'role_title': 'Engineer',
            'package_lpa': '5.00', 'min_cgpa': '6.00', 'max_backlogs': 0
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
