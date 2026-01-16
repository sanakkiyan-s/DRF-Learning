from rest_framework import viewsets, permissions, serializers
from django.utils import timezone
from .models import (
    User, Profile, UserSubscription, Genre, Movie, TVShow, Content,
    WatchHistory, WatchProgress, Rating, Review, UserContentInteraction
)
from .serializers import (
    UserSerializer, ProfileSerializer, 
    GenreSerializer, MovieSerializer, TVShowSerializer,
    WatchHistorySerializer, WatchProgressSerializer, RatingSerializer,
    ReviewSerializer, WatchlistSerializer
)
from rest_framework.response import Response
from rest_framework import status


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


# ==================== USER INTERACTION VIEWSETS ====================
class ProfileMixin:
    """Mixin to get the active profile from request headers."""
    def get_profile(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        if not profile_id:
            raise serializers.ValidationError("X-Profile-ID header is required.")
        try:
            return Profile.objects.get(id=profile_id, user=self.request.user)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Invalid profile.")


class WatchHistoryViewSet(ProfileMixin, viewsets.ModelViewSet):
    """Track what the profile has watched."""
    serializer_class = WatchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        profile = self.get_profile()
        return WatchHistory.objects.filter(profile=profile).select_related('content')

    def perform_create(self, serializer):
        profile = self.get_profile()
        content = Content.objects.get(id=serializer.validated_data['content_id'])
        serializer.save(profile=profile, content=content)


class WatchProgressViewSet(ProfileMixin, viewsets.ModelViewSet):
    """Resume playback - Continue Watching feature."""
    serializer_class = WatchProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head']
    lookup_field = 'content_id'

    def get_queryset(self):
        profile = self.get_profile()
        return WatchProgress.objects.filter(profile=profile).select_related('content')

    def perform_create(self, serializer):
        profile = self.get_profile()
        content = Content.objects.get(id=serializer.validated_data['content_id'])
        # Use update_or_create for upsert
        obj, created = WatchProgress.objects.update_or_create(
            profile=profile,
            content=content,
            defaults={'resume_time_seconds': serializer.validated_data['resume_time_seconds']}
        )
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.perform_create(serializer)
        return Response(WatchProgressSerializer(obj).data, status=status.HTTP_200_OK)


class RatingViewSet(ProfileMixin, viewsets.ModelViewSet):
    """Rate content (1-5 stars)."""
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = self.get_profile()
        return Rating.objects.filter(profile=profile).select_related('content')

    def perform_create(self, serializer):
        profile = self.get_profile()
        content = Content.objects.get(id=serializer.validated_data['content_id'])
        # Upsert rating
        obj, created = Rating.objects.update_or_create(
            profile=profile,
            content=content,
            defaults={'rating_value': serializer.validated_data['rating_value']}
        )
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.perform_create(serializer)
        return Response(RatingSerializer(obj).data, status=status.HTTP_200_OK)


class ReviewViewSet(ProfileMixin, viewsets.ModelViewSet):
    """Write and manage reviews."""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = self.get_profile()
        return Review.objects.filter(profile=profile).select_related('content', 'profile')

    def perform_create(self, serializer):
        profile = self.get_profile()
        content = Content.objects.get(id=serializer.validated_data['content_id'])
        serializer.save(profile=profile, content=content)


class WatchlistViewSet(ProfileMixin, viewsets.ModelViewSet):
    """Manage watchlist (add/remove content to watch later)."""
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head']

    def get_queryset(self):
        profile = self.get_profile()
        return UserContentInteraction.objects.filter(
            profile=profile, is_in_watchlist=True
        ).select_related('content')

    def perform_create(self, serializer):
        profile = self.get_profile()
        content = Content.objects.get(id=serializer.validated_data['content_id'])
        obj, created = UserContentInteraction.objects.update_or_create(
            profile=profile,
            content=content,
            defaults={'is_in_watchlist': True}
        )
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.perform_create(serializer)
        return Response(WatchlistSerializer(obj).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_in_watchlist = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)