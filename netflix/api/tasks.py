from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_async(self, subject, template_name, context, recipient_email):
    """
    Async email sending task to prevent webhook timeouts.
    Retries up to 3 times with 60 second delays.
    """
    try:
        context['frontend_url'] = settings.FRONTEND_URL
        message = render_to_string(f'subscription/{template_name}', context)
        
        send_mail(
            subject=subject,
            message='',  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=message

        )
        logger.info(f"Email sent: {subject} to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        raise self.retry(exc=e)


@shared_task
def check_trial_endings():
    """
    Daily task: Send reminders for trials ending in 3 days.
    Run via Celery Beat: every day at 9 AM.
    """
    from .models import UserSubscription
    
    three_days_from_now = timezone.now() + timedelta(days=3)
    ending_soon = UserSubscription.objects.filter(
        status=UserSubscription.SubscriptionStatus.TRIALING,
        trial_end__date=three_days_from_now.date()
    ).select_related('user', 'subscription_plan')
    
    count = 0
    for sub in ending_soon:
        send_email_async.delay(
            subject=f'Your {sub.subscription_plan.name} trial ends soon',
            template_name='trial_ending_email.html',
            context={
                'user': {'email': sub.user.email},
                'plan': {'name': sub.subscription_plan.name},
                'trial_end': sub.trial_end.isoformat()
            },
            recipient_email=sub.user.email
        )
        count += 1
    
    logger.info(f"Sent {count} trial ending reminders")
    return count


@shared_task
def check_expiring_subscriptions():
    """
    Daily task: Check and expire subscriptions past their end date.
    """
    from .models import UserSubscription
    
    now = timezone.now()
    expired = UserSubscription.objects.filter(
        status__in=[
            UserSubscription.SubscriptionStatus.ACTIVE,
            UserSubscription.SubscriptionStatus.TRIALING
        ],
        current_period_end__lt=now
    )
    
    count = expired.update(status=UserSubscription.SubscriptionStatus.EXPIRED)
    logger.info(f"Expired {count} subscriptions")
    return count


@shared_task
def cleanup_old_stripe_events():
    """
    Weekly task: Remove Stripe events older than 30 days.
    Keeps database clean while maintaining recent idempotency.
    """
    from .models import StripeEvent
    
    cutoff = timezone.now() - timedelta(days=30)
    count, _ = StripeEvent.objects.filter(processed_at__lt=cutoff).delete()
    logger.info(f"Cleaned up {count} old Stripe events")
    return count


# Optional: Celery Beat schedule configuration
# Add to settings.py:
#
# CELERY_BEAT_SCHEDULE = {
#     'check-trial-endings': {
#         'task': 'api.tasks.check_trial_endings',
#         'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
#     },
#     'check-expiring-subscriptions': {
#         'task': 'api.tasks.check_expiring_subscriptions',
#         'schedule': crontab(hour=0, minute=0),  # Daily at midnight
#     },
#     'cleanup-stripe-events': {
#         'task': 'api.tasks.cleanup_old_stripe_events',
#         'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Weekly on Sunday 3 AM
#     },
# }
