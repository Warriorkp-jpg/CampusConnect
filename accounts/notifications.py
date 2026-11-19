from .models import Notification


def notify_user(user, title, message, category='GENERAL'):
    if user and getattr(user, 'is_active', True):
        return Notification.objects.create(
            user=user,
            title=title[:120],
            message=message[:500],
            category=category,
        )
    return None
