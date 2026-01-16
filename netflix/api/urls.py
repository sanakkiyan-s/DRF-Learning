from .views import (
    UserView, ProfileView, GenreViewSet, MovieViewSet, TVShowViewSet,
    WatchHistoryViewSet, WatchProgressViewSet, RatingViewSet, ReviewViewSet, WatchlistViewSet
)
from .views_stripe import (
    StripeCheckoutView, StripeWebhookView, VerifyStripeSessionView, 
    SubscriptionPlanListView, SubscriptionStatusView, ManageSubscriptionView, BillingHistoryView
)
from .views_device import (
    DeviceTokenObtainPairView, ProfileSelectView, StreamLogoutView, ActiveStreamsView
)
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter



router = DefaultRouter()
router.register('accounts', UserView, basename='account')
router.register('profiles', ProfileView, basename='profile')
router.register('genres', GenreViewSet, basename='genre')
router.register('movies', MovieViewSet, basename='movie')
router.register('tv-shows', TVShowViewSet, basename='tv-show')
router.register('watch-history', WatchHistoryViewSet, basename='watch-history')
router.register('watch-progress', WatchProgressViewSet, basename='watch-progress')
router.register('ratings', RatingViewSet, basename='rating')
router.register('reviews', ReviewViewSet, basename='review')
router.register('watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', DeviceTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('profile/select/', ProfileSelectView.as_view(), name='profile-select'),
    path('stream/logout/', StreamLogoutView.as_view(), name='stream-logout'),
    path('stream/active/', ActiveStreamsView.as_view(), name='active-streams'),


    path('payment/stripe/checkout/', StripeCheckoutView.as_view(), name='stripe-checkout'),
    path('payment/stripe/verify-session/', VerifyStripeSessionView.as_view(), name='stripe-verify-session'),
    path('payment/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),

    
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/manage/', ManageSubscriptionView.as_view(), name='subscription-manage'),
    path('subscription/billing-history/', BillingHistoryView.as_view(), name='billing-history'),
]


    
