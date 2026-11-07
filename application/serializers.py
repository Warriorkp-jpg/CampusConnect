from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    STATUS_TRANSITIONS = {
        'APPLIED': {'SHORTLISTED', 'REJECTED'},
        'SHORTLISTED': {'SELECTED', 'REJECTED'},
        'SELECTED': set(),
        'REJECTED': set(),
    }

    student_name = serializers.ReadOnlyField(source='student.get_full_name')
    student_roll_number = serializers.ReadOnlyField(source='student.roll_number')
    student_email = serializers.ReadOnlyField(source='student.email')
    student_cgpa = serializers.ReadOnlyField(source='student.cgpa')
    student_backlogs = serializers.ReadOnlyField(source='student.backlogs')
    company_name = serializers.ReadOnlyField(source='drive.company_name')
    role_title = serializers.ReadOnlyField(source='drive.role_title')

    class Meta:
        model = Application
        fields = (
            'id', 'student', 'student_name', 'student_roll_number', 'student_email',
            'student_cgpa', 'student_backlogs', 'drive', 'company_name', 'role_title',
            'status', 'applied_at'
        )
        read_only_fields = (
            'id', 'student', 'student_name', 'student_roll_number', 'student_email',
            'student_cgpa', 'student_backlogs', 'company_name', 'role_title',
            'applied_at'
        )

    def validate(self, attrs):
        if self.instance is not None:
            next_status = self.initial_data.get('status')
            if next_status and next_status != self.instance.status:
                allowed = self.STATUS_TRANSITIONS[self.instance.status]
                if next_status not in allowed:
                    raise serializers.ValidationError({
                        'status': f'Cannot change {self.instance.status} to {next_status}.'
                    })
                attrs['status'] = next_status
            return attrs

        student = self.context['request'].user
        drive = attrs['drive']
        if not drive.is_open:
            raise serializers.ValidationError({'drive': 'This placement drive is closed.'})
        if Application.objects.filter(student=student, drive=drive).exists():
            raise serializers.ValidationError({'drive': 'You have already applied to this drive.'})
        if student.cgpa < drive.min_cgpa:
            raise serializers.ValidationError({
                'cgpa': f'Your CGPA ({student.cgpa}) is below the required {drive.min_cgpa}.'
            })
        if student.backlogs > drive.max_backlogs:
            raise serializers.ValidationError({
                'backlogs': f'Maximum allowed backlogs: {drive.max_backlogs}.'
            })
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is None:
            fields['status'].read_only = True
        else:
            fields['drive'].read_only = True
        return fields
