from rest_framework import serializers
from .models import Drive

class DriveSerializer(serializers.ModelSerializer):
    posted_by = serializers.ReadOnlyField(source = 'posted_by.username')
    
    class Meta:
        model = Drive
        fields = '__all__'
    
        