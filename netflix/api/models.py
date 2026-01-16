import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.utils import timezone


# ==================== CUSTOM USER MANAGER ====================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)


class StripeEvent(models.Model):
    """
    Track processed Stripe webhook events to prevent duplicate processing.
    Critical for webhook idempotency.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stripe_event'
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['processed_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.event_id}"


# ==================== USER MODEL ====================
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Payment Info
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['country_code']
    
    class Meta:
        db_table = 'user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['country_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.email


# ==================== PROFILE MODEL ====================
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=50)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    language_code = models.CharField(max_length=2, default='en')
    is_kid_profile = models.BooleanField(default=False)
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'profile'
        unique_together = [['user', 'name']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_kid_profile']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


# ==================== SUBSCRIPTION MODELS ====================
class SubscriptionPlan(models.Model):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending'
        CANCELED = 'canceled', 'Canceled'
        EXPIRED = 'expired', 'Expired'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_concurrent_streams = models.IntegerField(default=1)
    max_profiles = models.IntegerField(default=1)
    supports_uhd = models.BooleanField(default=False)
    supports_hdr = models.BooleanField(default=False)
    supports_dolby_atmos = models.BooleanField(default=False)
    allows_downloads = models.BooleanField(default=False)
    max_download_devices = models.IntegerField(default=0)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Payment Gateway IDs
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True, null=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True, null=True)
    
    # Trial period
    trial_days = models.IntegerField(default=0, help_text="Number of free trial days (0 = no trial)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plan'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price_monthly']),
            models.Index(fields=['is_active']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending'
        TRIALING = 'trialing', 'Trialing'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELED = 'canceled', 'Canceled'
        EXPIRED = 'expired', 'Expired'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Payment Info
    payment_method_last_four = models.CharField(max_length=4, blank=True, null=True)
    payment_method_type = models.CharField(max_length=20, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscription'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['current_period_end']),
            models.Index(fields=['status', 'current_period_end']),
            models.Index(fields=['stripe_subscription_id']),  # Critical for webhook lookups
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.name}"


class BillingHistory(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_history')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    billing_cycle_start = models.DateTimeField()
    billing_cycle_end = models.DateTimeField()
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    payment_gateway_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'billing_history'
        indexes = [
            models.Index(fields=['user', 'billing_cycle_start']),
            models.Index(fields=['invoice_number']),
        ]
        ordering = ['-billing_cycle_start']
    
    def __str__(self):
        return f"{self.user.email} - {self.invoice_number}"


# ==================== CONTENT MODELS ====================
class MaturityLevel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    minimum_age = models.IntegerField()
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'maturity_level'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['minimum_age']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Content(models.Model):
    class ContentType(models.TextChoices):
        MOVIE = 'movie', 'Movie'
        TV_SHOW = 'tv_show', 'TV Show'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    release_date = models.DateField(blank=True, null=True)
    duration_minutes = models.IntegerField(blank=True, null=True)
    poster_image_url = models.URLField(max_length=500, blank=True, null=True)
    backdrop_image_url = models.URLField(max_length=500, blank=True, null=True)
    trailer_url = models.URLField(max_length=500, blank=True, null=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    maturity_level = models.ForeignKey(MaturityLevel, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'content'
        indexes = [
            models.Index(fields=['release_date']),
            models.Index(fields=['content_type']),
            models.Index(fields=['maturity_level']),
            models.Index(fields=['release_date', 'content_type']),
            models.Index(fields=['is_deleted', 'release_date']),
        ]
    
    def __str__(self):
        return self.title


class Movie(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True, related_name='movie_details')
    director = models.CharField(max_length=255, blank=True, null=True)
    budget = models.BigIntegerField(blank=True, null=True)
    box_office_revenue = models.BigIntegerField(blank=True, null=True)
    awards = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'movie'
    
    def __str__(self):
        return self.content.title


class TVShow(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True, related_name='tv_show_details')
    total_seasons = models.IntegerField(default=1)
    total_episodes = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='ongoing')
    
    class Meta:
        db_table = 'tv_show'
    
    def __str__(self):
        return self.content.title


class Season(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='seasons')
    season_number = models.IntegerField()
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'season'
        unique_together = [['tv_show', 'season_number']]
        indexes = [
            models.Index(fields=['tv_show']),
            models.Index(fields=['season_number']),
            models.Index(fields=['release_date']),
        ]
    
    def __str__(self):
        return f"{self.tv_show.content.title} - Season {self.season_number}"


class Episode(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True, related_name='episode_details')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'episode'
        unique_together = [['season', 'episode_number']]
        indexes = [
            models.Index(fields=['season']),
            models.Index(fields=['episode_number']),
        ]
    
    def __str__(self):
        return f"{self.season.tv_show.content.title} S{self.season.season_number}E{self.episode_number}"


# ==================== CONTENT METADATA MODELS ====================
class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'genre'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        return self.name


class ContentGenre(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'content_genre'
        unique_together = [['content', 'genre']]
        indexes = [
            models.Index(fields=['content']),
            models.Index(fields=['genre']),
        ]
    
    def __str__(self):
        return f"{self.content.title} - {self.genre.name}"


class CastMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=True, null=True)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cast_member'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['birth_date']),
        ]
    
    def __str__(self):
        return self.name


class ContentCast(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    cast_member = models.ForeignKey(CastMember, on_delete=models.CASCADE)
    character_name = models.CharField(max_length=255, blank=True, null=True)
    role_type = models.CharField(max_length=50, default='actor')
    billing_order = models.IntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'content_cast'
        unique_together = [['content', 'cast_member', 'role_type']]
        indexes = [
            models.Index(fields=['content']),
            models.Index(fields=['cast_member']),
            models.Index(fields=['billing_order']),
        ]
    
    def __str__(self):
        return f"{self.content.title} - {self.cast_member.name} ({self.role_type})"


# ==================== USER INTERACTION MODELS ====================
class WatchHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='watch_history')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='watch_history')
    watch_started_at = models.DateTimeField()
    watch_ended_at = models.DateTimeField(blank=True, null=True)
    watched_seconds = models.IntegerField(default=0)
    start_position_seconds = models.IntegerField(blank=True, null=True)
    end_position_seconds = models.IntegerField(blank=True, null=True)
    device = models.ForeignKey('Device', on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watch_history'
        indexes = [
            models.Index(fields=['profile', '-watch_started_at']),
            models.Index(fields=['content', '-watch_started_at']),
            models.Index(fields=['profile', 'content', '-watch_started_at']),
        ]
        ordering = ['-watch_started_at']
    
    def __str__(self):
        return f"{self.profile.name} watched {self.content.title}"


class WatchProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='watch_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='watch_progress')
    resume_time_seconds = models.IntegerField(default=0)
    last_watched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'watch_progress'
        unique_together = [['profile', 'content']]
        indexes = [
            models.Index(fields=['profile', 'content'], name='ux_watch_progress'),
        ]
    
    def __str__(self):
        return f"{self.profile.name} - {self.content.title} at {self.resume_time_seconds}s"


class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ratings')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='ratings')
    rating_value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    rated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rating'
        unique_together = [['profile', 'content']]
        indexes = [
            models.Index(fields=['content']),
            models.Index(fields=['content', 'rating_value']),
        ]
    
    def __str__(self):
        return f"{self.profile.name} rated {self.content.title} {self.rating_value}/5"


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='reviews')
    title = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()
    contains_spoilers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review'
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['content']),
            models.Index(fields=['content', 'created_at']),
            models.Index(fields=['profile', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.profile.name}'s review of {self.content.title}"


class UserContentInteraction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='content_interactions')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='user_interactions')
    total_watch_time_seconds = models.IntegerField(default=0)
    watch_count = models.IntegerField(default=0)
    last_watched_at = models.DateTimeField(blank=True, null=True)
    is_in_watchlist = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_content_interaction'
        unique_together = [['profile', 'content']]
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['content']),
            models.Index(fields=['profile', 'updated_at']),
            models.Index(fields=['content', 'total_watch_time_seconds']),
        ]
    
    def __str__(self):
        return f"{self.profile.name} - {self.content.title}"


# ==================== DEVICE MODELS ====================
class Device(models.Model):
    class DeviceType(models.TextChoices):
        SMART_TV = 'smart_tv', 'Smart TV'
        MOBILE = 'mobile', 'Mobile'
        TABLET = 'tablet', 'Tablet'
        DESKTOP = 'desktop', 'Desktop'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    device_name = models.CharField(max_length=100)
    device_model = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    app_version = models.CharField(max_length=20, blank=True, null=True)
    last_login_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device'
        unique_together = [['user', 'device_name']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['device_type']),
            models.Index(fields=['user', 'last_login_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.device_type})"


class DeviceLogin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='logins')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='device_logins')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location_country = models.CharField(max_length=2, blank=True, null=True)
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'device_login'
        indexes = [
            models.Index(fields=['device']),
            models.Index(fields=['profile']),
            models.Index(fields=['device', 'login_at']),
            models.Index(fields=['profile', 'login_at']),
        ]
        ordering = ['-login_at']
    
    def __str__(self):
        return f"{self.profile.name} on {self.device.device_name} at {self.login_at}"


# ==================== DOWNLOAD MODEL ====================
class Download(models.Model):
    class VideoQuality(models.TextChoices):
        SD = 'SD', 'Standard Definition'
        HD = 'HD', 'High Definition'
        FHD = 'FHD', 'Full HD'
        UHD = 'UHD', 'Ultra HD'
    
    class DownloadStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        DOWNLOADING = 'downloading', 'Downloading'
        COMPLETED = 'completed', 'Completed'
        EXPIRED = 'expired', 'Expired'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='downloads')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='downloads')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='downloads')
    video_quality = models.CharField(max_length=10, choices=VideoQuality.choices)
    file_size_bytes = models.BigIntegerField(blank=True, null=True)
    download_path = models.CharField(max_length=500, blank=True, null=True)
    download_status = models.CharField(
        max_length=20, 
        choices=DownloadStatus.choices, 
        default=DownloadStatus.PENDING
    )
    progress_percentage = models.IntegerField(default=0)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'download'
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['device']),
            models.Index(fields=['profile', 'downloaded_at']),
            models.Index(fields=['expires_at', 'download_status']),
        ]
    
    def __str__(self):
        return f"{self.profile.name} - {self.content.title} ({self.video_quality})"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_be_played(self):
        return (
            self.download_status == Download.DownloadStatus.COMPLETED 
            and not self.is_expired()
        )