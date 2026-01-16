import stripe
import json
import logging
import uuid
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import get_user_model

from .models import UserSubscription, SubscriptionPlan, BillingHistory, StripeEvent
from .serializers import SubscriptionPlanSerializer
from rest_framework import generics
from .tasks import send_email_async

logger = logging.getLogger(__name__)

# Get User model safely
User = get_user_model()


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]


class SubscriptionStatusView(APIView):
    """Netflix-like subscription status with streaming permissions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        
        # Get all user subscriptions ordered by recency
        subscriptions = UserSubscription.objects.filter(user=user).order_by('-current_period_end', '-created_at')
        
        # Check for active subscription
        active_sub = subscriptions.filter(status=UserSubscription.SubscriptionStatus.ACTIVE).first()
        
        if active_sub:
            # Validate expiry
            if not active_sub.current_period_end or active_sub.current_period_end < now:
                with transaction.atomic():
                    active_sub.status = UserSubscription.SubscriptionStatus.EXPIRED
                    active_sub.save()
                return Response({
                    'status': 'expired',
                    'plan_name': active_sub.subscription_plan.name,
                    'current_period_end': active_sub.current_period_end,
                    'can_stream': False
                })
            
            days_until_expiry = (active_sub.current_period_end - now).days
            warning_message = None
            
            if 0 < days_until_expiry <= 7:
                warning_message = f'Subscription renews in {days_until_expiry} days'
            
            if active_sub.cancel_at_period_end:
                warning_message = f'Subscription ends in {days_until_expiry} days'
            
            return Response({
                'status': 'active',
                'plan_name': active_sub.subscription_plan.name,
                'current_period_end': active_sub.current_period_end,
                'days_until_renewal': days_until_expiry,
                'cancel_at_period_end': active_sub.cancel_at_period_end,
                'warning': warning_message,
                'can_stream': True,
                'max_streams': active_sub.subscription_plan.max_concurrent_streams
            })
        
        # Check for trialing
        trialing_sub = subscriptions.filter(status=UserSubscription.SubscriptionStatus.TRIALING).first()
        if trialing_sub:
            trial_days_left = (trialing_sub.trial_end - now).days if trialing_sub.trial_end else 0
            return Response({
                'status': 'trialing',
                'plan_name': trialing_sub.subscription_plan.name,
                'trial_end': trialing_sub.trial_end,
                'trial_days_left': max(0, trial_days_left),
                'can_stream': True,
                'max_streams': trialing_sub.subscription_plan.max_concurrent_streams
            })
        
        # Check for pending
        pending_sub = subscriptions.filter(status=UserSubscription.SubscriptionStatus.PENDING).first()
        if pending_sub:
            return Response({
                'status': 'processing',
                'plan_name': pending_sub.subscription_plan.name,
                'message': 'Subscription is being processed',
                'can_stream': False
            })
        
        # Check for past due (grace period)
        past_due_sub = subscriptions.filter(status=UserSubscription.SubscriptionStatus.PAST_DUE).first()
        if past_due_sub:
            return Response({
                'status': 'past_due',
                'plan_name': past_due_sub.subscription_plan.name,
                'message': 'Payment failed. Please update payment method.',
                'can_stream': True  # Grace period
            })
        
        return Response({
            'status': 'inactive',
            'plan_name': None,
            'message': 'No active subscription',
            'can_stream': False
        })


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_checkout_session(user, plan_id, interval='monthly'):
    """Create Stripe checkout session with trial support"""
    try:
        plan_obj = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        raise ValueError('Invalid Plan ID')
    
    if not plan_obj.is_active:
        raise ValueError('This plan is not available')

    stripe_price_id = plan_obj.stripe_price_id_monthly if interval == 'monthly' else plan_obj.stripe_price_id_yearly
    
    if not stripe_price_id:
        raise ValueError('Stripe Price ID not configured')

    # Get or create Stripe customer
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={'user_id': str(user.id)},
            name=user.email
        )
        user.stripe_customer_id = customer.id
        user.save()
    
    customer_id = user.stripe_customer_id
    idempotency_key = f"checkout-{user.id}-{plan_obj.id}-{interval}-{uuid.uuid4()}"
    
    subscription_data = {
        'metadata': {
            'user_id': str(user.id),
            'plan_id': str(plan_obj.id),
            'interval': interval
        }
    }
    
    # Add trial if configured
    if plan_obj.trial_days and plan_obj.trial_days > 0:
        subscription_data['trial_period_days'] = plan_obj.trial_days
    
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{'price': stripe_price_id, 'quantity': 1}],
        mode='subscription',
        success_url=settings.FRONTEND_URL + '/subscription/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=settings.FRONTEND_URL + '/subscription/plans',
        subscription_data=subscription_data,
        metadata={
            'user_id': str(user.id),
            'plan_id': str(plan_obj.id),
            'interval': interval
        },
        idempotency_key=idempotency_key
    )
    return checkout_session


class StripeCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            plan_id = request.data.get('plan_id')
            interval = request.data.get('interval', 'monthly')
            
            if not plan_id:
                return Response({'error': 'Plan ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Prevent multiple active subscriptions
            active_exists = UserSubscription.objects.filter(
                user=user,
                status__in=[UserSubscription.SubscriptionStatus.ACTIVE, UserSubscription.SubscriptionStatus.TRIALING]
            ).exists()
            
            if active_exists:
                return Response({
                    'error': 'You already have an active subscription',
                    'action': 'manage'
                }, status=status.HTTP_400_BAD_REQUEST)

            checkout_session = create_stripe_checkout_session(user, plan_id, interval)
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Checkout error: {e}", exc_info=True)
            return Response({'error': 'Checkout failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManageSubscriptionView(APIView):
    """Manage subscription: cancel, reactivate, access portal"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get Stripe billing portal URL"""
        user = request.user
        
        if not user.stripe_customer_id:
            return Response({'error': 'No billing account found'}, status=404)
        
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=settings.FRONTEND_URL + '/settings',
            )
            return Response({'portal_url': portal_session.url})
        except stripe.error.StripeError as e:
            logger.error(f"Stripe portal error: {e}")
            return Response({'error': 'Unable to load billing portal'}, status=500)
    
    def post(self, request):
        """Cancel or reactivate subscription"""
        user = request.user
        action = request.data.get('action', 'cancel')
        
        subscription = UserSubscription.objects.filter(
            user=user,
            status__in=[UserSubscription.SubscriptionStatus.ACTIVE, UserSubscription.SubscriptionStatus.PAST_DUE]
        ).first()
        
        if not subscription:
            return Response({'error': 'No active subscription'}, status=404)
        
        try:
            if action == 'cancel':
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
                subscription.save()
                
                return Response({
                    'message': 'Subscription will cancel at end of billing period',
                    'end_date': subscription.current_period_end
                })
            
            elif action == 'reactivate':
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=False
                )
                subscription.cancel_at_period_end = False
                subscription.save()
                
                return Response({'message': 'Subscription reactivated'})
            
            return Response({'error': 'Invalid action'}, status=400)
        
        except stripe.error.StripeError as e:
            logger.error(f"Subscription management error: {e}")
            return Response({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return HttpResponse(status=400)
        
        # Webhook idempotency
        event_id = event.get('id')
        event_type = event.get('type')
        
        if event_id:
            if StripeEvent.objects.filter(event_id=event_id).exists():
                return HttpResponse(status=200)
            
            try:
                with transaction.atomic():
                    StripeEvent.objects.create(event_id=event_id, event_type=event_type)
            except Exception:
                return HttpResponse(status=200)
            
            logger.info(f"Processing {event_type} ({event_id})")

        try:
            handlers = {
                'checkout.session.completed': self.handle_checkout_completed,
                'invoice.payment_succeeded': self.handle_payment_succeeded,
                'invoice.payment_failed': self.handle_payment_failed,
                'customer.subscription.deleted': self.handle_subscription_deleted,
                'customer.subscription.updated': self.handle_subscription_updated,
                'customer.subscription.trial_will_end': self.handle_trial_will_end,
            }
            
            handler = handlers.get(event_type)
            if handler:
                handler(event['data']['object'])
        
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            # If processing failed, remove the event marker so retry can happen
            if event_id:
                StripeEvent.objects.filter(event_id=event_id).delete()
            return HttpResponse(status=500)

        return HttpResponse(status=200)

    def handle_checkout_completed(self, session):
        subscription_id = session.get('subscription')
        if not subscription_id:
            return

        try:
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            meta = stripe_sub.get('metadata', {})
            user_id = meta.get('user_id') or session.get('metadata', {}).get('user_id')
            plan_id = meta.get('plan_id') or session.get('metadata', {}).get('plan_id')

            if not user_id or not plan_id:
                logger.warning(f"Missing metadata for {subscription_id}")
                return
            
            user_obj = User.objects.get(id=user_id)
            plan_obj = SubscriptionPlan.objects.get(id=plan_id)

            item = stripe_sub['items']['data'][0]
            cpe = datetime.fromtimestamp(item['current_period_end'], tz=dt_timezone.utc)
            cps = datetime.fromtimestamp(item['current_period_start'], tz=dt_timezone.utc)
            
            is_trial = stripe_sub.status == 'trialing'
            is_active = stripe_sub.status == 'active'
            trial_end = None
            if is_trial and stripe_sub.get('trial_end'):
                trial_end = datetime.fromtimestamp(stripe_sub['trial_end'], tz=dt_timezone.utc)
            
            # Set status based on Stripe's actual subscription status
            if is_trial:
                initial_status = UserSubscription.SubscriptionStatus.TRIALING
            elif is_active:
                initial_status = UserSubscription.SubscriptionStatus.ACTIVE
            else:
                initial_status = UserSubscription.SubscriptionStatus.PENDING
            
            with transaction.atomic():
                UserSubscription.objects.get_or_create(
                    stripe_subscription_id=subscription_id,
                    defaults={
                        'user_id': user_id,
                        'subscription_plan_id': plan_id,
                        'status': initial_status,
                        'current_period_start': cps,
                        'current_period_end': cpe,
                        'trial_end': trial_end,
                        'payment_method_type': 'stripe'
                    }
                )
            
            logger.info(f"Created subscription {subscription_id}")
            
            # Send Welcome/Trial Email
            email_template = 'trial_started_email.html' if is_trial else 'welcome_email.html'
            context = {
                'user': user_obj.email.split('@')[0],
                'plan_name': plan_obj.name,
                'trial_end_date': trial_end.strftime('%B %d, %Y') if trial_end else None,
                'login_url': settings.FRONTEND_URL + '/login'
            }
            send_email_async.delay(
                subject='Welcome to Netflix Clone',
                template_name=email_template,
                context=context,
                recipient_email=user_obj.email
            )

        except Exception as e:
            logger.error(f"Checkout completion error: {e}", exc_info=True)

    def handle_payment_succeeded(self, invoice):
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            # Fallback 1: try lines direct
            lines = invoice.get('lines', {}).get('data', [])
            if lines:
                subscription_id = lines[0].get('subscription')
            
            # Fallback 2: try lines parent
            if not subscription_id and lines:
                period = lines[0].get('parent', {}).get('subscription_item_details', {})
                subscription_id = period.get('subscription')
                
            # Fallback 3: try invoice parent
            if not subscription_id:
                parent = invoice.get('parent', {}).get('subscription_details', {})
                subscription_id = parent.get('subscription')
        
        invoice_number = invoice.get('number')
        
        if invoice.get('paid') is False:
            return
        
        if not subscription_id:
            return
        
        if BillingHistory.objects.filter(invoice_number=invoice_number).exists():
            return
            
        # Try to find existing subscription
        user_sub = UserSubscription.objects.filter(stripe_subscription_id=subscription_id).first()
        
        if not user_sub:
            # If not found, fetch details from Stripe to create it
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            meta = stripe_sub.get('metadata', {})
            user_id = meta.get('user_id')
            plan_id = meta.get('plan_id')
            
            if not user_id or not plan_id:
                return
            
            item = stripe_sub['items']['data'][0]
            user_sub = UserSubscription.objects.create(
                stripe_subscription_id=subscription_id,
                user_id=user_id,
                subscription_plan_id=plan_id,
                status=UserSubscription.SubscriptionStatus.PENDING,
                current_period_start=datetime.fromtimestamp(item['current_period_start'], tz=dt_timezone.utc),
                current_period_end=datetime.fromtimestamp(item['current_period_end'], tz=dt_timezone.utc),
                payment_method_type='stripe'
            )
        
        with transaction.atomic():
            user_sub.status = UserSubscription.SubscriptionStatus.ACTIVE
            user_sub.save()
        
            # Create billing history
            amount_paid = invoice.get('amount_paid', 0) / 100
            lines = invoice.get('lines', {}).get('data', [])
            if lines:
                period = lines[0].get('period', {})
                start_ts = period.get('start')
                end_ts = period.get('end')
            else:
                start_ts = invoice.get('period_start')
                end_ts = invoice.get('period_end')

            BillingHistory.objects.create(
                user=user_sub.user,
                subscription_plan=user_sub.subscription_plan,
                amount=amount_paid,
                    currency=invoice.get('currency', 'usd').upper(),
                    payment_status=BillingHistory.PaymentStatus.COMPLETED,
                    billing_cycle_start=datetime.fromtimestamp(start_ts, tz=dt_timezone.utc) if start_ts else timezone.now(),
                    billing_cycle_end=datetime.fromtimestamp(end_ts, tz=dt_timezone.utc) if end_ts else timezone.now(),
                    invoice_number=invoice_number,
                    payment_gateway_transaction_id=invoice.get('payment_intent')
                )
            
            logger.info(f"Payment succeeded for {subscription_id}")
            
            # Send Payment Receipt Email
            send_email_async.delay(
                subject='Payment Receipt',
                template_name='payment_receipt_email.html',
                context={
                    'user': user_sub.user.email.split('@')[0],
                    'amount': amount_paid,
                    'currency': invoice.get('currency', 'usd').upper(),
                    'date': datetime.now().strftime('%B %d, %Y'),
                    'invoice_number': invoice_number
                },
                recipient_email=user_sub.user.email
            )

    def handle_payment_failed(self, invoice):
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        try:
            with transaction.atomic():
                user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
                user_sub.status = UserSubscription.SubscriptionStatus.PAST_DUE
                user_sub.save()
            logger.warning(f"Payment failed for {subscription_id}")
            
            # Send Payment Failed Email
            send_email_async.delay(
                subject='Payment Failed',
                template_name='payment_failed_email.html',
                context={
                    'user': user_sub.user.email.split('@')[0],
                    'plan_name': user_sub.subscription_plan.name,
                    'payment_url': settings.FRONTEND_URL + '/billing'
                },
                recipient_email=user_sub.user.email
            )
        except UserSubscription.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Payment failure error: {e}", exc_info=True)

    def handle_subscription_updated(self, subscription):
        subscription_id = subscription.get('id')
        print(f"DEBUG: Webhook Update Entry {subscription_id}. Status: {subscription.get('status')}, CancelAtEnd: {subscription.get('cancel_at_period_end')}") # DEBUG LINE
        
        try:
            sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            
            status_map = {
                'active': UserSubscription.SubscriptionStatus.ACTIVE,
                'trialing': UserSubscription.SubscriptionStatus.TRIALING,
                'past_due': UserSubscription.SubscriptionStatus.PAST_DUE,
                'unpaid': UserSubscription.SubscriptionStatus.EXPIRED,
                'canceled': UserSubscription.SubscriptionStatus.CANCELED,
                'incomplete': UserSubscription.SubscriptionStatus.PENDING,
                'incomplete_expired': UserSubscription.SubscriptionStatus.EXPIRED
            }
            
            print(f"DEBUG: Webhook Update {subscription_id}. Status: {subscription.get('status')}, CancelAtEnd: {subscription.get('cancel_at_period_end')}") # DEBUG LINE
            
            sub.status = status_map.get(subscription.get('status'), UserSubscription.SubscriptionStatus.PENDING)
        
            # Check both boolean and timestamp for cancellation
            cancel_at_period_end = subscription.get('cancel_at_period_end', False)
            cancel_at = subscription.get('cancel_at')
            if cancel_at and not cancel_at_period_end:
                # If there's a specific cancel date in the future, treat as cancelling
                 cancel_at_period_end = True
                 
            sub.cancel_at_period_end = cancel_at_period_end
            
            cpe = subscription.get('current_period_end')
            cps = subscription.get('current_period_start')
            if cpe:
                sub.current_period_end = datetime.fromtimestamp(cpe, tz=dt_timezone.utc)
            if cps:
                sub.current_period_start = datetime.fromtimestamp(cps, tz=dt_timezone.utc)
            
            with transaction.atomic():
                sub.save()
            
            logger.info(f"Updated subscription {subscription_id}")
            
        except UserSubscription.DoesNotExist:
            pass

    def handle_subscription_deleted(self, subscription):
        subscription_id = subscription.get('id')
        try:
            sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            with transaction.atomic():
                sub.status = UserSubscription.SubscriptionStatus.CANCELED
                sub.current_period_end = timezone.now()
                sub.save()
            logger.info(f"Canceled subscription {subscription_id}")
        except UserSubscription.DoesNotExist:
            pass

    def handle_trial_will_end(self, subscription):
        """Handle trial ending in 3 days"""
        subscription_id = subscription.get('id')
        trial_end = subscription.get('trial_end')
        
        if not trial_end:
            return
        
        try:
            sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            trial_end_date = datetime.fromtimestamp(trial_end, tz=dt_timezone.utc)
            logger.info(f"Trial ending for {subscription_id} on {trial_end_date}")
            
            # Send Trial Ending Email
            send_email_async.delay(
                subject='Your Trial is Ending Soon',
                template_name='trial_ending_email.html',
                context={
                    'user': sub.user.email.split('@')[0],
                    'plan_name': sub.subscription_plan.name,
                    'trial_end_date': trial_end_date.strftime('%B %d, %Y'),
                    'amount': sub.subscription_plan.price_monthly 
                },
                recipient_email=sub.user.email
            )
        except UserSubscription.DoesNotExist:
            pass


class VerifyStripeSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        user = request.user
        
        try:
            # Check for active subscription (DB only)
            sub = UserSubscription.objects.filter(
                user=user,
                status__in=[
                    UserSubscription.SubscriptionStatus.ACTIVE,
                    UserSubscription.SubscriptionStatus.TRIALING
                ]
            ).first()
            
            if sub:
                return Response({
                    'status': 'active',
                    'plan_name': sub.subscription_plan.name,
                    'can_stream': True
                })
            
            # Check for pending
            pending = UserSubscription.objects.filter(
                user=user,
                status=UserSubscription.SubscriptionStatus.PENDING
            ).first()
            
            if pending:
                return Response({'status': 'processing'}, status=202)
            
            # Verify session once with caching
            if session_id:
                cache_key = f"session_{session_id}_{user.id}"
                cached = cache.get(cache_key)
                
                if cached is None:
                    try:
                        session = stripe.checkout.Session.retrieve(session_id)
                        if session.customer != user.stripe_customer_id:
                            return Response({'error': 'Invalid session'}, status=403)
                        cached = session.payment_status
                        cache.set(cache_key, cached, 30)
                    except stripe.error.StripeError:
                        pass
                
                if cached == 'paid':
                    return Response({'status': 'processing'}, status=202)
            
            return Response({'status': 'inactive'}, status=404)

        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=500)


class BillingHistoryView(APIView):
    """View billing/payment history"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = BillingHistory.objects.filter(
            user=request.user
        ).order_by('-billing_cycle_start')[:50]
        
        data = [{
            'date': bill.billing_cycle_start,
            'amount': float(bill.amount),
            'currency': bill.currency,
            'plan': bill.subscription_plan.name,
            'status': bill.payment_status,
            'invoice_number': bill.invoice_number
        } for bill in history]
        
        return Response(data)
