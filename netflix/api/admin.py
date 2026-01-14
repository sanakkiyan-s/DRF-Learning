from django.contrib import admin
from django.utils import timezone

from .models import (
    User, Profile, SubscriptionPlan, UserSubscription, BillingHistory, StripeEvent,
    MaturityLevel, Content, Movie, TVShow, Season, Episode,
    Genre, ContentGenre, CastMember, ContentCast,
    WatchHistory, WatchProgress, Rating, Review, UserContentInteraction,
    Device, DeviceLogin, Download
)


# Enhanced User Admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created_at', 'stripe_customer_id']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'stripe_customer_id']
    readonly_fields = ['created_at', 'last_login']


# Netflix-style Subscription Plan Admin
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_monthly', 'max_concurrent_streams', 'trial_days', 'is_active', 'display_order']
    list_filter = ['is_active', 'supports_uhd', 'supports_hdr']
    list_editable = ['display_order', 'is_active']
    search_fields = ['name']


# Enhanced Subscription Admin with actions
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_plan', 'status', 'current_period_end', 'trial_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'cancel_at_period_end', 'subscription_plan']
    search_fields = ['user__email', 'stripe_subscription_id']
    readonly_fields = ['stripe_subscription_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    actions = ['cancel_subscription', 'extend_trial', 'mark_active']
    
    @admin.action(description='Cancel selected subscriptions')
    def cancel_subscription(self, request, queryset):
        count = queryset.update(status='canceled', current_period_end=timezone.now())
        self.message_user(request, f'{count} subscription(s) canceled.')
    
    @admin.action(description='Extend trial by 7 days')
    def extend_trial(self, request, queryset):
        from datetime import timedelta
        for sub in queryset:
            if sub.trial_end:
                sub.trial_end = sub.trial_end + timedelta(days=7)
            else:
                sub.trial_end = timezone.now() + timedelta(days=7)
            sub.status = 'trialing'
            sub.save()
        self.message_user(request, f'{queryset.count()} subscription(s) trial extended.')
    
    @admin.action(description='Mark as active')
    def mark_active(self, request, queryset):
        count = queryset.update(status='active')
        self.message_user(request, f'{count} subscription(s) marked active.')


# Billing History Admin
@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_plan', 'amount', 'currency', 'payment_status', 'invoice_number', 'billing_cycle_start']
    list_filter = ['payment_status', 'currency', 'billing_cycle_start']
    search_fields = ['user__email', 'invoice_number']
    readonly_fields = ['invoice_number', 'payment_gateway_transaction_id', 'created_at']
    date_hierarchy = 'billing_cycle_start'


# Stripe Event Admin (for debugging webhooks)
@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'event_type', 'processed_at']
    list_filter = ['event_type', 'processed_at']
    search_fields = ['event_id']
    readonly_fields = ['event_id', 'event_type', 'processed_at']
    date_hierarchy = 'processed_at'


# Register remaining models with basic admin
admin.site.register(Profile)
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
