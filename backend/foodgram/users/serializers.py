from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from .models import Follower, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        model = User


class UserSuccesfullSignUpSerializer(UserSerializer):
    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
        )
        model = User


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(required=False)

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )
        model = User

    def get_is_subscribed(self, instance):
        user = self.context["request"].user
        author = instance
        if (
            not isinstance(user, AnonymousUser)
            and Follower.objects.filter(author=author, follower=user).exists()
        ):
            return True
        else:
            return False
