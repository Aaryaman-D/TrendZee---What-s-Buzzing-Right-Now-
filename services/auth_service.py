from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from accounts.models import CustomUser


class AuthService:

    @staticmethod
    def send_verification_email(request, user):
        """Send email verification link to user."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = settings.SITE_DOMAIN
        verification_url = f"http://{domain}/accounts/verify/{uid}/{token}/"

        subject = 'Verify your TrendZee account'
        message = render_to_string('accounts/emails/verification_email.txt', {
            'user': user,
            'verification_url': verification_url,
        })

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    @staticmethod
    def verify_email_token(uidb64, token):
        """Validate email verification token."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return {'success': False, 'message': 'Invalid verification link.'}

        if user.is_verified:
            return {'success': True, 'message': 'Email already verified.'}

        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            return {'success': True, 'message': 'Email verified successfully!'}

        return {'success': False, 'message': 'Verification link has expired. Please request a new one.'}

    @staticmethod
    def resend_verification(request, email):
        """Resend verification email if user exists and is unverified."""
        try:
            user = CustomUser.objects.get(email=email, is_verified=False)
            AuthService.send_verification_email(request, user)
        except CustomUser.DoesNotExist:
            pass  # Silent - don't leak user existence
