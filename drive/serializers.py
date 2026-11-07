from rest_framework import serializers
from .models import Drive


class DriveSerializer(serializers.ModelSerializer):
    posted_by = serializers.ReadOnlyField(source='posted_by.username')
    recruiter_company = serializers.ReadOnlyField(source='posted_by.company_name')
    is_open = serializers.ReadOnlyField()

    class Meta:
        model = Drive
        fields = (
            'id', 'company_name', 'role_title', 'description', 'location',
            'package_lpa', 'min_cgpa', 'max_backlogs', 'application_deadline',
            'is_active', 'is_open', 'posted_by', 'recruiter_company', 'created_at'
        )
        read_only_fields = ('id', 'posted_by', 'is_open', 'created_at')

    def validate(self, attrs):
        min_cgpa = attrs.get('min_cgpa', getattr(self.instance, 'min_cgpa', 0))
        if min_cgpa < 0 or min_cgpa > 10:
            raise serializers.ValidationError({'min_cgpa': 'Minimum CGPA must be between 0 and 10.'})
        if attrs.get('package_lpa', getattr(self.instance, 'package_lpa', 0)) < 0:
            raise serializers.ValidationError({'package_lpa': 'Package cannot be negative.'})
        return attrs
