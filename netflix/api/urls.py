from .views import AccountView
from django.urls import path, include

from rest_framework.routers import DefaultRouter

# urls.py in your DRF app
from django.urls import path
# from .views import CreateSubscriptionView, subscription_callback

# urlpatterns = [
#     path('create-subscription/', CreateSubscriptionView.as_view(), name='create-subscription'),
#     path('callback/', subscription_callback, name='subscription-callback'),
# ]

router = DefaultRouter()
router.register('accounts', AccountView, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]


    
