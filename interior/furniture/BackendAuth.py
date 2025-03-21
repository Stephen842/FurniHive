from django.contrib.auth.backends import BaseBackend
from .models import MyUsers

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Allow users to log in with either email or username (case insensitive)."""
        try:
            username = username.lower() # Ensure case insensitivity

            # Check if input is an email or username
            if '@' in username:
                user = MyUsers.objects.get(email=username) # Fetch user by email
            else:
                user = MyUsers.objects.get(username=username) # Fetch user by username

            # Verify password
            if user and user.check_password(password):
                return user
        except MyUsers.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return MyUsers.objects.get(pk=user_id)
        except MyUsers.DoesNotExist:
            return None