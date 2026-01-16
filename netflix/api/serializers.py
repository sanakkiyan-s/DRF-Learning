from rest_framework import serializers
from .models import (
    User, SubscriptionPlan, BillingHistory, UserSubscription, Profile,
    MaturityLevel, Genre, Content, Movie, TVShow, Season, Episode, ContentGenre,
    CastMember, ContentCast, WatchHistory, WatchProgress, Rating, Review, UserContentInteraction
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'country_code', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'avatar_url', 'language_code', 'is_kid_profile', 'age']



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class BillingHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    
    class Meta:
        model = BillingHistory
        fields = [
            'id', 'billing_cycle_start', 'billing_cycle_end', 'amount', 
            'currency', 'payment_status', 'invoice_number', 'plan_name', 'created_at'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    max_streams = serializers.IntegerField(source='subscription_plan.max_concurrent_streams', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'status', 'plan_name', 'current_period_start', 'current_period_end',
            'trial_end', 'cancel_at_period_end', 'max_streams', 'created_at'
        ]


class MaturityLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaturityLevel
        fields = ['code', 'name', 'minimum_age']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class CastMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CastMember
        fields = ['id', 'name', 'profile_image_url']


class ContentCastSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='cast_member.name')
    profile_image_url = serializers.URLField(source='cast_member.profile_image_url')
    
    class Meta:
        model = ContentCast
        fields = ['name', 'profile_image_url', 'character_name', 'role_type', 'billing_order']


class ContentSerializer(serializers.ModelSerializer):
    maturity_level = MaturityLevelSerializer(read_only=True)
    genres = serializers.SerializerMethodField()
    cast = ContentCastSerializer(source='contentcast_set', many=True, read_only=True)
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'description', 'content_type', 'release_date', 
            'duration_minutes', 'poster_image_url', 'backdrop_image_url', 
            'trailer_url', 'maturity_level', 'genres', 'cast'
        ]

    def get_genres(self, obj):
        # Optimized to avoid N+1 if prefetch_related is used
        return [cg.genre.name for cg in obj.contentgenre_set.all()]


class MovieSerializer(ContentSerializer):
    director = serializers.CharField(source='movie_details.director')
    
    class Meta(ContentSerializer.Meta):
        fields = ContentSerializer.Meta.fields + ['director']


class EpisodeSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='content.title')
    description = serializers.CharField(source='content.description')
    duration_minutes = serializers.IntegerField(source='content.duration_minutes')
    
    class Meta:
        model = Episode
        fields = ['episode_number', 'title', 'description', 'duration_minutes']


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Season
        fields = ['id', 'season_number', 'title', 'description', 'release_date', 'episodes']


class TVShowSerializer(ContentSerializer):
    seasons = SeasonSerializer(many=True, read_only=True, source='tv_show_details.seasons')
    total_seasons = serializers.IntegerField(source='tv_show_details.total_seasons')
    total_episodes = serializers.IntegerField(source='tv_show_details.total_episodes')
    status = serializers.CharField(source='tv_show_details.status')
    
    class Meta(ContentSerializer.Meta):
        fields = ContentSerializer.Meta.fields + ['total_seasons', 'total_episodes', 'status', 'seasons']


# ==================== USER INTERACTION SERIALIZERS ====================
class ContentMiniSerializer(serializers.ModelSerializer):
    """Lightweight Content serializer for embedding in interaction responses."""
    class Meta:
        model = Content
        fields = ['id', 'title', 'poster_image_url', 'content_type', 'duration_minutes']


class WatchHistorySerializer(serializers.ModelSerializer):
    content = ContentMiniSerializer(read_only=True)
    content_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = WatchHistory
        fields = [
            'id', 'content', 'content_id', 'watch_started_at', 'watch_ended_at',
            'watched_seconds', 'start_position_seconds', 'end_position_seconds'
        ]
        read_only_fields = ['id']


class WatchProgressSerializer(serializers.ModelSerializer):
    content = ContentMiniSerializer(read_only=True)
    content_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = WatchProgress
        fields = ['id', 'content', 'content_id', 'resume_time_seconds', 'last_watched_at']
        read_only_fields = ['id', 'last_watched_at']


class RatingSerializer(serializers.ModelSerializer):
    content_id = serializers.UUIDField(write_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'content_id', 'content_title', 'rating_value', 'rated_at']
        read_only_fields = ['id', 'rated_at']


class ReviewSerializer(serializers.ModelSerializer):
    content_id = serializers.UUIDField(write_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'content_id', 'content_title', 'profile_name',
            'title', 'body', 'contains_spoilers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WatchlistSerializer(serializers.ModelSerializer):
    content = ContentMiniSerializer(read_only=True)
    content_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserContentInteraction
        fields = ['id', 'content', 'content_id', 'is_in_watchlist', 'created_at']
        read_only_fields = ['id', 'created_at']