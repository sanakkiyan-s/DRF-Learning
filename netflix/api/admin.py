from django.contrib import admin

# Register your models here.
from .models import (
    User, Profile, SubscriptionPlan, UserSubscription, BillingHistory,
    MaturityLevel, Content, Movie, TVShow, Season, Episode,
    Genre, ContentGenre, CastMember, ContentCast,
    WatchHistory, WatchProgress, Rating, Review, UserContentInteraction,
    Device, DeviceLogin, Download
)

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(BillingHistory)
admin.site.register(MaturityLevel)
admin.site.register(Content)
admin.site.register(Movie)
admin.site.register(TVShow)
admin.site.register(Season)
admin.site.register(Episode)
admin.site.register(Genre)
admin.site.register(ContentGenre)
admin.site.register(CastMember)
admin.site.register(ContentCast)
admin.site.register(WatchHistory)
admin.site.register(WatchProgress)
admin.site.register(Rating)
admin.site.register(Review)
admin.site.register(UserContentInteraction)
admin.site.register(Device)
admin.site.register(DeviceLogin)
admin.site.register(Download)
