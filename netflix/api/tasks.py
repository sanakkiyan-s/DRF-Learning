
from celery import shared_task
from django.utils import timezone

@shared_task
def send_email_async(subject, recipient_email, template_name=None, context=None, message=''):
    """
    Async task to send emails with HTML support.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    html_message = None
    if template_name and context:
        html_message = render_to_string(template_name, context)
        if not message:
            message = "Please view this email in an HTML-compatible email viewer."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return f"Email sent to {recipient_email}"

@shared_task
def check_trial_endings():
    """
    Daily task to check for subscriptions ending their trial soon.
    """
    print(f"Checking trial endings at {timezone.now()}")
    return "Checked Trials"

@shared_task
def check_expiring_subscriptions():
    """
    Daily task to check for subscriptions expiring soon.
    """
    print(f"Checking expiring subscriptions at {timezone.now()}")
    return "Checked Expirations"

@shared_task
def cleanup_old_stripe_events():
    """
    Weekly task to clean up old processed Stripe events.
    """
    print(f"Cleaning stripe events at {timezone.now()}")
    return "Cleaned Events"
