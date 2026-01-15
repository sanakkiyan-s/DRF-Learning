from rest_framework import viewsets, permissions, serializers
from django.utils import timezone
from .models import User, Profile, UserSubscription, Genre, Movie, TVShow, Content
from .serializers import (
    UserSerializer, ProfileSerializer, 
    GenreSerializer, MovieSerializer, TVShowSerializer
)


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


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all().order_by('display_order', 'name')
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticated]


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve movies.
    Filter by genre using ?genre=Action
    """
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Content.objects.filter(content_type=Content.ContentType.MOVIE).select_related(
            'movie_details', 'maturity_level'
        ).prefetch_related(
            'contentgenre_set__genre',
            'contentcast_set__cast_member'
        ).all()
        
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(contentgenre_set__genre__name__iexact=genre)
            
        return queryset


class TVShowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve TV Shows.
    Detailed view includes seasons and episodes.
    """
    serializer_class = TVShowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Content.objects.filter(content_type=Content.ContentType.TV_SHOW).select_related(
            'tv_show_details', 'maturity_level'
        ).prefetch_related(
            'contentgenre_set__genre',
            'contentcast_set__cast_member',
            'tv_show_details__seasons',
            'tv_show_details__seasons__episodes',
            'tv_show_details__seasons__episodes__content'
        ).all()
        
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(contentgenre_set__genre__name__iexact=genre)
            
        return queryset