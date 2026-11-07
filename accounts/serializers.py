from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import StudentRoster

User = get_user_model()


class StudentRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('roll_number', 'email', 'password')

    def validate_roll_number(self, value):
        value = value.strip().upper()
        try:
            record = StudentRoster.objects.get(roll_number__iexact=value)
        except StudentRoster.DoesNotExist:
            raise serializers.ValidationError(
                'This roll number is not present in the JMIT student roster. Contact the TPO office.'
            )
        if record.student_user_id:
            raise serializers.ValidationError('This roll number is already registered.')
        self.context['roster_record'] = record
        return value

    def create(self, validated_data):
        record = self.context['roster_record']
        roll_number = validated_data['roll_number']
        user = User.objects.create_user(
            username=roll_number,
            roll_number=roll_number,
            email=validated_data.get('email') or record.college_email,
            password=validated_data['password'],
            role='STUDENT',
            cgpa=record.cgpa,
            backlogs=record.backlogs,
        )
        record.student_user = user
        record.save(update_fields=['student_user'])
        return user


class RecruiterRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'company_name', 'phone_number')

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data, role='RECRUITER', recruiter_status='PENDING'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'roll_number', 'company_name',
            'phone_number', 'recruiter_status', 'cgpa', 'backlogs'
        )
        read_only_fields = fields


class StudentRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRoster
        fields = ('id', 'roll_number', 'full_name', 'college_email', 'program', 'batch', 'cgpa', 'backlogs', 'student_user')
        read_only_fields = ('id', 'student_user')

    def validate_cgpa(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('CGPA must be between 0 and 10.')
        return value


class RecruiterReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'company_name', 'phone_number', 'recruiter_status')
        read_only_fields = ('id', 'username', 'email', 'company_name', 'phone_number')

    def validate_recruiter_status(self, value):
        if value not in ('APPROVED', 'REJECTED'):
            raise serializers.ValidationError('Choose APPROVED or REJECTED.')
        return value


class CampusConnectTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept the student's roll number in the normal username login field."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['recruiter_status'] = user.recruiter_status
        return token

    def validate(self, attrs):
        username = attrs['username'].strip()
        if not User.objects.filter(username=username).exists():
            matched_student = User.objects.filter(roll_number__iexact=username, role='STUDENT').first()
            if matched_student:
                username = matched_student.username
        attrs['username'] = username
        return super().validate(attrs)
