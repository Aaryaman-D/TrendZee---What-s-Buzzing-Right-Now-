import re
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser


def validate_real_email(email):
    """
    Strict email validation:
    - Must match standard email format
    - Local part must not be purely numeric or have suspicious patterns
    - Domain must be a proper TLD domain (no IP, no multi-dot tricks)
    """
    # Standard email regex
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,63}@[a-zA-Z0-9][a-zA-Z0-9\-]{0,253}\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Enter a valid email address (e.g. name@domain.com).")

    local, domain = email.rsplit('@', 1)

    # Reject emails where local part is purely digits
    if re.match(r'^\d+$', local):
        raise ValidationError("Email address appears invalid. Please use a real email.")

    # Reject consecutive dots
    if '..' in email:
        raise ValidationError("Email address cannot contain consecutive dots.")

    # Reject domains like "in.com" stuffed before @gmail.com (e.g. 123.in.com@gmail.com)
    # Local part should not contain a domain-like pattern
    if re.search(r'\.[a-z]{2,6}\.[a-z]{2,6}$', local, re.IGNORECASE):
        raise ValidationError(
            "Email address format looks suspicious. Please enter your actual email address."
        )

    # Domain must have at least one dot with valid TLD
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        raise ValidationError("Email domain is invalid.")

    tld = domain_parts[-1]
    if len(tld) < 2 or not tld.isalpha():
        raise ValidationError("Email domain has an invalid extension.")

    # Reject known disposable/fake patterns in local part
    suspicious_patterns = [
        r'^\d{3,}\..*',    # starts with 3+ digits then dot
        r'.*\..*\..*@',    # multiple dots making fake sub-domains in local
    ]
    for p in suspicious_patterns:
        if re.match(p, local, re.IGNORECASE):
            raise ValidationError(
                "Please enter a valid email address. Addresses like '123.in.com@gmail.com' are not accepted."
            )


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a strong password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        validate_real_email(email)
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_password2(self):
        pw1 = self.cleaned_data.get('password1')
        pw2 = self.cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError("Passwords do not match.")
        return pw2

    def clean_password1(self):
        pw = self.cleaned_data.get('password1')
        if pw:
            password_validation.validate_password(pw)
        return pw

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_verified = False
        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Your password'}),
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
        existing = CustomUser.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError("This username is already taken.")
        return username
