from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from .models import UserSubscription, SubscriptionPlan, BillingHistory
from django.utils import timezone
import json
import datetime
from datetime import timezone as dt_timezone

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
    def test_webhook_checkout_session_completed_new_sub(self, mock_retrieve_sub, mock_construct_event):
        # 1. Checkout Session Completed
        # Mock payload
        payload = {
            'id': 'evt_test_checkout',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'subscription': 'sub_new_123',
                    # We fallback to session metadata if needed, but logic prefers sub metadata
                    'metadata': {
                         'user_id': str(self.user.id),
                         'plan_id': str(self.plan.id)
                    }
                }
            }
        }
        mock_construct_event.return_value = payload

        # Mock Stripe Subscription details
        mock_sub = MagicMock()
        sub_data = {
            'metadata': {'user_id': str(self.user.id), 'plan_id': str(self.plan.id)},
            'items': {'data': [{
                'current_period_end': 1700000000, 
                'current_period_start': 1600000000
            }]},
            'current_period_end': 1700000000,
            'current_period_start': 1600000000
        }
        mock_sub.get.side_effect = sub_data.get
        mock_sub.__getitem__.side_effect = sub_data.__getitem__
        mock_retrieve_sub.return_value = mock_sub

        response = self.client.post(
            self.webhook_url, 
            data=json.dumps(payload), 
            content_type='application/json',
            **{'HTTP_STRIPE_SIGNATURE': 'valid'}
        )
        self.assertEqual(response.status_code, 200)

        # Verify UserSubscription created
        sub = UserSubscription.objects.get(stripe_subscription_id='sub_new_123')
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.current_period_end.timestamp(), 1700000000)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_succeeded(self, mock_construct_event):
        # Pre-create subscription
        UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            stripe_subscription_id='sub_existing_123',
            status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + datetime.timedelta(days=30),
            payment_method_type='stripe'
        )

        payload = {
            'id': 'evt_test_invoice',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'subscription': 'sub_existing_123',
                    'amount_paid': 1599,
                    'currency': 'usd',
                    'lines': {
                        'data': [{
                            'period': {
                                'start': 1610000000,
                                'end': 1612678400
                            }
                        }]
                    },
                    'number': 'INV-123',
                    'payment_intent': 'pi_123'
                }
            }
        }
        mock_construct_event.return_value = payload

        response = self.client.post(
            self.webhook_url, 
            data=json.dumps(payload), 
            content_type='application/json',
            **{'HTTP_STRIPE_SIGNATURE': 'valid'}
        )
        self.assertEqual(response.status_code, 200)

        # Verify BillingHistory created
        history = BillingHistory.objects.get(invoice_number='INV-123')
        self.assertEqual(history.user, self.user)
        self.assertEqual(float(history.amount), 15.99)
        self.assertEqual(history.billing_cycle_start.timestamp(), 1610000000)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_subscription_updated(self, mock_construct_event):
        # Pre-create subscription
        sub = UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            stripe_subscription_id='sub_renew_123',
            status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now()
        )

        payload = {
            'id': 'evt_test_updated',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_renew_123',
                    'status': 'active',
                    'current_period_end': 1800000000 # New date
                }
            }
        }
        mock_construct_event.return_value = payload

        response = self.client.post(
            self.webhook_url, 
            data=json.dumps(payload), 
            content_type='application/json',
            **{'HTTP_STRIPE_SIGNATURE': 'valid'}
        )
        self.assertEqual(response.status_code, 200)

        sub.refresh_from_db()
        self.assertEqual(sub.current_period_end.timestamp(), 1800000000)
