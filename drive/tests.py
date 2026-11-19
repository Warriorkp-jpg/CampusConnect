from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Drive


class StudentDriveEligibilityTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='ELIGIBLE001', roll_number='ELIGIBLE001',
            password='StrongPass123', role='STUDENT',
            cgpa=Decimal('8.00'), backlogs=1
        )
        self.tpo = User.objects.create_user(
            username='eligibility_tpo', password='StrongPass123', role='TPO'
        )
        self.eligible = Drive.objects.create(
            company_name='Eligible Co', role_title='Python Developer',
            package_lpa=6, min_cgpa=7, max_backlogs=1, posted_by=self.tpo
        )
        self.cgpa_ineligible = Drive.objects.create(
            company_name='High CGPA Co', role_title='Engineer',
            package_lpa=8, min_cgpa=9, max_backlogs=2, posted_by=self.tpo
        )
        self.backlog_ineligible = Drive.objects.create(
            company_name='No Backlogs Co', role_title='Analyst',
            package_lpa=5, min_cgpa=6, max_backlogs=0, posted_by=self.tpo
        )

    def test_student_only_sees_drives_they_are_eligible_for(self):
        self.client.force_authenticate(self.student)
        response = self.client.get('/api/drive/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([item['id'] for item in results], [self.eligible.id])
