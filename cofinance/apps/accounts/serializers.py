from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("email", "phone", "first_name", "last_name", "region", "role", "password")
        read_only_fields = ("role",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "phone", "first_name", "last_name",
            "full_name", "role", "region", "is_online", "date_joined",
        )
        read_only_fields = ("id", "role", "is_online", "date_joined")

    def get_full_name(self, obj):
        return obj.get_full_name()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "region")
