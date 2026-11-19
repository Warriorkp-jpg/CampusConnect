from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import override_settings
import re
from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User, StudentRoster
from drive.models import Drive
from application.models import Application


class RegistrationWorkflowTests(APITestCase):
    def test_student_registration_requires_verified_roster_email(self):
        response = self.client.post('/api/register/student/', {
            'challenge_id': '00000000-0000-0000-0000-000000000000',
            'password': 'StrongPass123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        record = StudentRoster.objects.create(
            roll_number='JMIT001', full_name='Test Student',
            college_email='student@jmit.example',
            cgpa=Decimal('8.25'), backlogs=0
        )
        response = self.client.post('/api/register/student/', {
            'challenge_id': '00000000-0000-0000-0000-000000000000',
            'password': 'StrongPass123', 'email': 'attacker@example.com',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(roll_number='JMIT001').exists())
        self.assertIsNone(record.student_user_id)

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



class StudentRosterBulkImportTests(APITestCase):
    def setUp(self):
        self.tpo = User.objects.create_user(
            username='roster_tpo', password='StrongPass123', role='TPO'
        )
        self.client.force_authenticate(self.tpo)

    def upload_csv(self, content, filename='roster.csv'):
        upload = SimpleUploadedFile(
            filename, content.encode('utf-8'), content_type='text/csv'
        )
        return self.client.post(
            '/api/tpo/student-roster/import/',
            {'file': upload},
            format='multipart'
        )

    def test_imports_valid_rows_and_reports_invalid_rows(self):
        response = self.upload_csv(
            'roll_number,full_name,college_email,cgpa,backlogs\n'
            'JMIT101,Student One,one@jmit.example,8.25,0\n'
            'JMIT102,,two@jmit.example,7.50,0\n'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['error_count'], 1)
        self.assertTrue(StudentRoster.objects.filter(roll_number='JMIT101').exists())
        self.assertFalse(StudentRoster.objects.filter(roll_number='JMIT102').exists())

    def test_existing_roster_records_are_skipped_not_overwritten(self):
        StudentRoster.objects.create(
            roll_number='JMIT201', full_name='Original Name', cgpa=Decimal('7.00')
        )
        response = self.upload_csv(
            'roll_number,full_name,college_email\nJMIT201,Changed Name,old@jmit.example\nJMIT202,New Student,new@jmit.example\n'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['skipped_existing'], 1)
        original = StudentRoster.objects.get(roll_number='JMIT201')
        self.assertEqual(original.full_name, 'Original Name')

    def test_rejects_unsupported_file_type(self):
        response = self.upload_csv('roll_number,full_name\nJMIT301,Student\n', 'roster.txt')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_tpo_can_import_roster(self):
        student = User.objects.create_user(
            username='roster_student', roll_number='S900',
            password='StrongPass123', role='STUDENT'
        )
        self.client.force_authenticate(student)
        response = self.upload_csv('roll_number,full_name\nS901,Student\n')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class StudentEmailOTPTests(APITestCase):
    def setUp(self):
        self.record = StudentRoster.objects.create(
            roll_number='JMITOTP001',
            full_name='OTP Student',
            college_email='otp.student@jmit.example',
            cgpa=Decimal('8.40'),
            backlogs=0,
        )

    def request_otp(self):
        return self.client.post(
            '/api/register/student/request-otp/',
            {'roll_number': self.record.roll_number},
            format='json',
        )

    def test_student_can_verify_roster_email_and_register(self):
        request_response = self.request_otp()
        self.assertEqual(request_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        challenge_id = request_response.data['challenge_id']
        otp_match = re.search(r'\b(\d{6})\b', mail.outbox[0].body)
        self.assertIsNotNone(otp_match)

        verify_response = self.client.post(
            '/api/register/student/verify-otp/',
            {'challenge_id': challenge_id, 'otp': otp_match.group(1)},
            format='json',
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        register_response = self.client.post(
            '/api/register/student/',
            {
                'challenge_id': challenge_id,
                'password': 'StrongPass123',
                'email': 'attacker@example.com',
                'role': 'TPO',
            },
            format='json',
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(roll_number=self.record.roll_number)
        self.record.refresh_from_db()
        self.assertEqual(user.email, self.record.college_email)
        self.assertEqual(user.role, 'STUDENT')
        self.assertEqual(user.cgpa, self.record.cgpa)
        self.assertEqual(user.backlogs, self.record.backlogs)
        self.assertEqual(self.record.student_user_id, user.id)

    def test_wrong_otp_is_rejected(self):
        response = self.request_otp()
        actual = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
        wrong = f'{(int(actual) + 1) % 1000000:06d}'
        result = self.client.post(
            '/api/register/student/verify-otp/',
            {'challenge_id': response.data['challenge_id'], 'otp': wrong},
            format='json',
        )
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_roll_number_does_not_send_email(self):
        response = self.client.post(
            '/api/register/student/request-otp/',
            {'roll_number': 'UNKNOWN999'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_verified_challenge_cannot_be_reused(self):
        response = self.request_otp()
        otp_match = re.search(r'\b(\d{6})\b', mail.outbox[0].body)
        self.client.post(
            '/api/register/student/verify-otp/',
            {'challenge_id': response.data['challenge_id'], 'otp': otp_match.group(1)},
            format='json',
        )
        self.client.post(
            '/api/register/student/',
            {'challenge_id': response.data['challenge_id'], 'password': 'StrongPass123'},
            format='json',
        )
        replay = self.client.post(
            '/api/register/student/',
            {'challenge_id': response.data['challenge_id'], 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(replay.status_code, status.HTTP_400_BAD_REQUEST)



class StudentProfileAndResumeTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='PROFILE001', roll_number='PROFILE001',
            password='StrongPass123', role='STUDENT'
        )
        self.recruiter = User.objects.create_user(
            username='profile_recruiter', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Acme'
        )
        self.other_recruiter = User.objects.create_user(
            username='profile_other', password='StrongPass123',
            role='RECRUITER', recruiter_status='APPROVED', company_name='Other'
        )
        self.tpo = User.objects.create_user(
            username='profile_tpo', password='StrongPass123', role='TPO'
        )
        self.drive = Drive.objects.create(
            company_name='Acme', role_title='Developer', package_lpa=5,
            min_cgpa=0, max_backlogs=5, posted_by=self.recruiter
        )
        Application.objects.create(student=self.student, drive=self.drive)

    def test_student_can_save_profile_and_pdf_resume(self):
        self.client.force_authenticate(self.student)
        resume = SimpleUploadedFile(
            'my_resume.pdf',
            b'%PDF-1.4\n% CampusConnect test PDF',
            content_type='application/pdf',
        )
        response = self.client.patch(
            '/api/student-profile/',
            {
                'skills': 'Python, Django, SQL',
                'github_url': 'https://github.com/example',
                'linkedin_url': 'https://www.linkedin.com/in/example',
                'resume': resume,
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['resume_uploaded'])
        self.assertEqual(response.data['skills'], 'Python, Django, SQL')

    def test_only_student_owner_tpo_or_relevant_recruiter_can_download_resume(self):
        profile = StudentProfile.objects.create(user=self.student)
        profile.resume.save(
            'test.pdf',
            SimpleUploadedFile('test.pdf', b'%PDF-1.4\nTest file', content_type='application/pdf'),
        )

        self.client.force_authenticate(self.other_recruiter)
        denied = self.client.get(f'/api/students/{self.student.id}/resume/')
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.recruiter)
        allowed = self.client.get(f'/api/students/{self.student.id}/resume/')
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.tpo)
        tpo_allowed = self.client.get(f'/api/students/{self.student.id}/resume/')
        self.assertEqual(tpo_allowed.status_code, status.HTTP_200_OK)

    def test_student_cannot_upload_non_pdf_resume(self):
        self.client.force_authenticate(self.student)
        bad_file = SimpleUploadedFile(
            'resume.txt', b'not a pdf', content_type='text/plain'
        )
        response = self.client.patch(
            '/api/student-profile/', {'resume': bad_file}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
