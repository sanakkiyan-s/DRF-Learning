from rest_framework import viewsets, permissions, serializers
from django.utils import timezone
from .models import User, Profile, UserSubscription
from .serializers import UserSerializer, ProfileSerializer


class UserView(viewsets.ModelViewSet):
    """
    ViewSet for managing User accounts.
    Provides CRUD operations for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProfileView(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        
        # Check active subscription
        try:
            subscription = user.subscriptions.get(
                status=UserSubscription.SubscriptionStatus.ACTIVE,
                current_period_end__gt=timezone.now()
            )
        except UserSubscription.DoesNotExist:
            raise serializers.ValidationError(
                "Active subscription required to create profiles."
            )

        # Check profile limit
        current_profile_count = Profile.objects.filter(user=user).count()
        max_profiles = subscription.subscription_plan.max_profiles
        
        if current_profile_count >= max_profiles:
            raise serializers.ValidationError(
                f"Profile limit reached. Your plan allows a maximum of {max_profiles} profiles."
            )
            
        serializer.save(user=user)