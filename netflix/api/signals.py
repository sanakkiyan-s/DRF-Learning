from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import WatchHistory, WatchProgress, UserContentInteraction


@receiver(post_save, sender=WatchHistory)
def update_user_content_interaction(sender, instance, created, **kwargs):
    """
    When a WatchHistory record is saved, update the UserContentInteraction
    to aggregate watch stats (watch_count, total_watch_time, last_watched_at).
    """
    if not created:
        return  # Only process new records
    
    profile = instance.profile
    content = instance.content
    watched_seconds = instance.watched_seconds or 0
    
    # Get or create the interaction record
    interaction, _ = UserContentInteraction.objects.get_or_create(
        profile=profile,
        content=content,
        defaults={
            'total_watch_time_seconds': 0,
            'watch_count': 0,
        }
    )
    
    # Aggregate stats
    interaction.watch_count += 1
    interaction.total_watch_time_seconds += watched_seconds
    interaction.last_watched_at = timezone.now()
    interaction.save()
    
    # Check if video was finished (>= 95% watched)
    # and remove from Continue Watching if so
    _check_and_remove_completed_progress(instance, profile, content)


def _check_and_remove_completed_progress(watch_history, profile, content):
    """
    Remove WatchProgress if the user finished the video.
    Finished = end_position >= 95% of content duration.
    """
    end_position = watch_history.end_position_seconds
    duration = content.duration_minutes
    
    if not end_position or not duration:
        return
    
    duration_seconds = duration * 60
    completion_ratio = end_position / duration_seconds
    
    if completion_ratio >= 0.95:
        WatchProgress.objects.filter(
            profile=profile,
            content=content
        ).delete()
