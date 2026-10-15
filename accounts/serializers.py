from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    
    # send password in POST , and never include to JSON respoone
    password = serializers.CharField(write_only = True)
    
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'cgpa', 'backlogs']
    
    
    # by default create = User.ocjects.create(**validate_data)
    # cause plain pass but JWT want a hashed pass
        
    def create(self, validated_data):
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'STUDENT'),
            cgpa=validated_data.get('cgpa', 0.00),
            backlogs=validated_data.get('backlogs', 0),
        )
        
        return user