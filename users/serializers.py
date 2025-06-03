from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

User = get_user_model()


class LoginByEmailOrPhoneSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        password = attrs.get('password')
        user = None
        if '@' in email_or_phone:
            try:
                user = User.objects.get(email=email_or_phone)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(phone_number=email_or_phone)
            except User.DoesNotExist:
                pass
        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Unable to log in with provided credentials.')


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'email', 'phone_number', 'password')

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        first_name, *last_name = full_name.split(' ', 1)
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name[0] if last_name else '',
            bio='',
        )
        user.phone_number = validated_data['phone_number']
        user.set_password(validated_data['password'])
        user.save()
        return user


class ProfilePictureSerializer(serializers.ModelSerializer):
    avatar_sm = serializers.URLField(read_only=True)
    avatar_md = serializers.URLField(read_only=True)
    avatar_lg = serializers.URLField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['avatar', 'avatar_sm', 'avatar_md', 'avatar_lg']
