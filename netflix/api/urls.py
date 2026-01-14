from .views import UserView
from .views_stripe import (
    StripeCheckoutView, StripeWebhookView, VerifyStripeSessionView, 
    SubscriptionPlanListView, SubscriptionStatusView, ManageSubscriptionView, BillingHistoryView
)
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework.routers import DefaultRouter



router = DefaultRouter()
router.register('accounts', UserView, basename='account')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('payment/stripe/checkout/', StripeCheckoutView.as_view(), name='stripe-checkout'),
    path('payment/stripe/verify-session/', VerifyStripeSessionView.as_view(), name='stripe-verify-session'),
    path('payment/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/manage/', ManageSubscriptionView.as_view(), name='subscription-manage'),
    path('subscription/billing-history/', BillingHistoryView.as_view(), name='billing-history'),
]


    
