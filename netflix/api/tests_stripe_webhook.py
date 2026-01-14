from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from .models import UserSubscription, SubscriptionPlan
from django.utils import timezone
import json
import stripe

User = get_user_model()

class StripeWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com', 
            password='password123',
            country_code='US'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            price_monthly=15.99,
            display_order=1
        )
        self.client = Client()
        self.webhook_url = reverse('stripe-webhook')

    @patch('stripe.Webhook.construct_event')
    @patch('stripe.Subscription.retrieve')
    def test_webhook_checkout_session_completed(self, mock_retrieve_sub, mock_construct_event):
        # Mock the event payload
        payload = {
            'id': 'evt_test',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'subscription': 'sub_test_123',
                    'metadata': {
                        'user_id': str(self.user.id),
                        'plan_id': str(self.plan.id)
                    }
                }
            }
        }
        
        # Mock construct_event to return the event object from payload
        mock_construct_event.return_value = payload

        # Mock Stripe Subscription Retrieve
        mock_sub = MagicMock()
        mock_sub.get.side_effect = lambda k, d=None: {
            'current_period_end': timezone.now().timestamp() + 30*24*3600,
            'current_period_start': timezone.now().timestamp(),
            'items': {'data': [{'current_period_end': timezone.now().timestamp() + 30*24*3600, 'current_period_start': timezone.now().timestamp()}]}
        }.get(k, d)
        mock_retrieve_sub.return_value = mock_sub

        # Request
        headers = {'HTTP_STRIPE_SIGNATURE': 'valid_signature'}
        response = self.client.post(
            self.webhook_url, 
            data=json.dumps(payload), 
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, 200)

        # Assertion: Check if UserSubscription created
        self.assertTrue(UserSubscription.objects.filter(user=self.user).exists())
        sub = UserSubscription.objects.get(user=self.user)
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.stripe_subscription_id, 'sub_test_123')
        self.assertEqual(sub.subscription_plan, self.plan)
