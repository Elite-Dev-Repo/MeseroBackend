from django.core.mail import send_mail
from django.dispatch import receiver 
from django.db.models.signals import post_save
from .models import User, OTPToken
from django.utils import timezone
from django.conf import settings
import secrets


@receiver(post_save, sender=User)
def create_token(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            return
        OTPToken.objects.create(user=instance)
        instance.is_active = False
        instance.save()



@receiver(post_save, sender=OTPToken)
def send_verification_email(sender, instance, created, **kwargs):
    if not created:
        return
    subject = "Email Verification"
    recipient = [instance.user.email]
    body = f"""
    Hello {instance.user.first_name}, here is your email verification code {instance.token}.
    Go to  www.x_link.com/verification/ to verify
    """

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient,
        fail_silently=False
    )