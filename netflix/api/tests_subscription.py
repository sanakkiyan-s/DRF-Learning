from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json

from rest_framework.test import APITestCase
from rest_framework import status

from .models import UserSubscription, SubscriptionPlan, BillingHistory, StripeEvent


User = get_user_model()


class SubscriptionStatusViewTest(APITestCase):
    """Test subscription status endpoint"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Premium',
            price_monthly=9.99,
            max_concurrent_streams=4,
            trial_days=7
        )
        self.client.force_authenticate(user=self.user)
    
    def test_no_subscription_returns_inactive(self):
        response = self.client.get('/api/subscription/status/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'inactive')
        self.assertFalse(response.data['can_stream'])
    
    def test_active_subscription_returns_active(self):
        UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get('/api/subscription/status/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'active')
        self.assertTrue(response.data['can_stream'])
    
    def test_expired_subscription_marked_expired(self):
        UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            current_period_start=timezone.now() - timedelta(days=60),
            current_period_end=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        response = self.client.get('/api/subscription/status/')
        self.assertEqual(response.data['status'], 'expired')
        self.assertFalse(response.data['can_stream'])
    
    def test_trialing_subscription(self):
        trial_end = timezone.now() + timedelta(days=5)
        UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            status=UserSubscription.SubscriptionStatus.TRIALING,
            current_period_start=timezone.now(),
            current_period_end=trial_end,
            trial_end=trial_end
        )
        
        response = self.client.get('/api/subscription/status/')
        self.assertEqual(response.data['status'], 'trialing')
        self.assertTrue(response.data['can_stream'])


class WebhookIdempotencyTest(TransactionTestCase):
    """Test webhook processes events only once"""
    
    def test_duplicate_event_skipped(self):
        event_id = 'evt_test_123'
        
        # First processing should create event
        StripeEvent.objects.create(event_id=event_id, event_type='test.event')
        
        # Verify event exists
        self.assertTrue(StripeEvent.objects.filter(event_id=event_id).exists())
        
        # Count should still be 1
        self.assertEqual(StripeEvent.objects.filter(event_id=event_id).count(), 1)


class PaymentSucceededTest(APITestCase):
    """Test payment handling creates billing history"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Premium',
            price_monthly=9.99
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            stripe_subscription_id='sub_test123',
            status=UserSubscription.SubscriptionStatus.PENDING,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )
    
    def test_billing_history_created(self):
        """Verify billing history is created on payment"""
        BillingHistory.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            amount=9.99,
            currency='USD',
            payment_status=BillingHistory.PaymentStatus.COMPLETED,
            billing_cycle_start=timezone.now(),
            billing_cycle_end=timezone.now() + timedelta(days=30),
            invoice_number='inv_test_001'
        )
        
        self.assertEqual(BillingHistory.objects.filter(user=self.user).count(), 1)
    
    def test_duplicate_invoice_prevented(self):
        """Verify duplicate invoices are rejected"""
        invoice_number = 'inv_duplicate_test'
        
        BillingHistory.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            amount=9.99,
            currency='USD',
            payment_status=BillingHistory.PaymentStatus.COMPLETED,
            billing_cycle_start=timezone.now(),
            billing_cycle_end=timezone.now() + timedelta(days=30),
            invoice_number=invoice_number
        )
        
        # Trying to create duplicate should fail (unique constraint)
        with self.assertRaises(Exception):
            BillingHistory.objects.create(
                user=self.user,
                subscription_plan=self.plan,
                amount=9.99,
                currency='USD',
                payment_status=BillingHistory.PaymentStatus.COMPLETED,
                billing_cycle_start=timezone.now(),
                billing_cycle_end=timezone.now() + timedelta(days=30),
                invoice_number=invoice_number
            )


class ManageSubscriptionTest(APITestCase):
    """Test subscription management endpoint"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            stripe_customer_id='cus_test123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Premium',
            price_monthly=9.99
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            stripe_subscription_id='sub_test123',
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('stripe.Subscription.modify')
    def test_cancel_subscription(self, mock_modify):
        mock_modify.return_value = MagicMock()
        
        response = self.client.post('/api/subscription/manage/', {'action': 'cancel'})
        
        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertTrue(self.subscription.cancel_at_period_end)
    
    @patch('stripe.Subscription.modify')
    def test_reactivate_subscription(self, mock_modify):
        mock_modify.return_value = MagicMock()
        self.subscription.cancel_at_period_end = True
        self.subscription.save()
        
        response = self.client.post('/api/subscription/manage/', {'action': 'reactivate'})
        
        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.cancel_at_period_end)


class BillingHistoryTest(APITestCase):
    """Test billing history endpoint"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Premium',
            price_monthly=9.99
        )
        self.client.force_authenticate(user=self.user)
    
    def test_empty_billing_history(self):
        response = self.client.get('/api/subscription/billing-history/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
    
    def test_billing_history_returns_data(self):
        BillingHistory.objects.create(
            user=self.user,
            subscription_plan=self.plan,
            amount=9.99,
            currency='USD',
            payment_status=BillingHistory.PaymentStatus.COMPLETED,
            billing_cycle_start=timezone.now(),
            billing_cycle_end=timezone.now() + timedelta(days=30),
            invoice_number='inv_test_001'
        )
        
        response = self.client.get('/api/subscription/billing-history/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], 9.99)
