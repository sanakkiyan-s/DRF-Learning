from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer


class UserView(viewsets.ModelViewSet):
    """
    ViewSet for managing User accounts.
    Provides CRUD operations for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer