from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    # Read-only fields so the student only has to send {"drive": 1} in Postman!
    student_name = serializers.ReadOnlyField(source='student.username')
    company_name = serializers.ReadOnlyField(source='drive.company_name')
    role_title = serializers.ReadOnlyField(source='drive.role_title')

    class Meta:
        model = Application
        fields = [
            'id',
            'student',
            'student_name',
            'drive',
            'company_name',
            'role_title',
            'status',
            'applied_at',
        ]
        # The student cannot fake their own ID or manually set status to 'SELECTED'!
        read_only_fields = ['student', 'status', 'applied_at']

    def validate(self, data):
        # 1. Grab the logged-in student from the request context
        student = self.context['request'].user
        drive = data['drive']

        # 2. Check Duplicate Application
        if Application.objects.filter(student=student, drive=drive).exists():
            raise serializers.ValidationError(
                "You have already applied for this placement drive."
            )

        # 3. Check CGPA Eligibility
        if student.cgpa < drive.min_cgpa:
            raise serializers.ValidationError(
                f"Not Eligible: Your CGPA ({student.cgpa}) is less than the required CGPA ({drive.min_cgpa})."
            )

        # 4. Check Active Backlogs Eligibility
        if student.backlogs > drive.max_backlogs:
            raise serializers.ValidationError(
                f"Not Eligible: You have {student.backlogs} backlogs, but the maximum allowed is {drive.max_backlogs}."
            )

        return data