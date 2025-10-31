# Updated models.py with phone authentication support

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

DESIGN_CHOICES = [
    ('professional', 'Professional'),
    ('modern', 'Modern'),
    ('elegant', 'Elegant'),
]


class Certificate(models.Model):
    """Certificate model to store user certificates"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    CURRENCY_CHOICES = [
        ('KZT', 'Kazakhstan Tenge'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('RUB', 'Russian Ruble'),
    ]

    # Identification
    certificate_id = models.CharField(
        max_length=50, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        null=True,
        blank=True
    )

    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(
        max_length=20, blank=True, db_index=True)  # Added index for phone lookup

    # Certificate details
    recipient_name = models.CharField(max_length=100)
    certificate_text = models.TextField(max_length=300, blank=True)
    signature_text = models.CharField(max_length=100, blank=True)
    tree_count = models.PositiveIntegerField(default=1)
    template = models.ForeignKey(
        'CertificateTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    design = models.CharField(
        max_length=20, choices=DESIGN_CHOICES, default='professional')

    # Payment information
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='KZT')
    payment_id = models.CharField(max_length=100, blank=True)

    # Status tracking
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_phone', 'created_at']),
            models.Index(fields=['customer_email', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.recipient_name}"

    @property
    def environmental_impact(self):
        return {
            'co2_absorption_per_year': self.tree_count * 22,
            'oxygen_production_per_year': self.tree_count * 16,
            'air_for_people': self.tree_count * 2,
        }

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class CertificateTemplate(models.Model):
    """Certificate template with different designs and variations"""

    design = models.CharField(max_length=20, choices=DESIGN_CHOICES)
    variation = models.CharField(
        max_length=50,
        help_text="Введите имя сертификата, например: 'v1'",
        default="default"
    )
    name = models.CharField(max_length=100, blank=True,
                            help_text="Template display name")
    description = models.TextField(
        blank=True, help_text="Template description")
    background_image = models.ImageField(
        upload_to="certificate_templates/",
        blank=True,
        null=True,
        help_text="Upload certificate template background image"
    )
    is_active = models.BooleanField(default=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('design', 'variation')
        ordering = ['design', 'variation']

    def __str__(self):
        if self.name:
            return f"{self.get_design_display()} - {self.name}"
        return f"{self.get_design_display()} - {self.variation}"


class VolunteerApplication(models.Model):
    """Volunteer application form submissions"""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    region = models.CharField(max_length=50)
    dates = models.CharField(max_length=200, blank=True)
    experience = models.TextField(blank=True)
    submitted = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} – {self.region}"


class OrganizerApplication(models.Model):
    """Organizer application form submissions"""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    organization = models.CharField(max_length=150, blank=True)
    region = models.CharField(max_length=50)
    plan = models.TextField()
    submitted = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} – {self.region}"


# Optional: UserProfile for extended user information
class UserProfile(models.Model):
    """Extended user profile to store additional information"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    total_trees_planted = models.IntegerField(default=0)
    total_donations = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)

    # Preferences
    preferred_language = models.CharField(max_length=2, choices=[
        ('ru', 'Russian'),
        ('kz', 'Kazakh'),
        ('en', 'English')
    ], default='ru')

    # Notifications
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"

    constraints = [
        models.UniqueConstraint(
            fields=['phone_number'],
            condition=models.Q(phone_number__isnull=False),
            name='unique_non_null_phone'
        )
    ]

    def update_statistics(self):
        """Update user statistics from certificates"""
        certificates = Certificate.objects.filter(
            user=self.user, status='completed')
        self.total_trees_planted = sum(
            cert.tree_count for cert in certificates)
        self.total_donations = sum(cert.total_amount for cert in certificates)
        self.save()

    def get_visible_email(self):
        """Возвращает email с частичным скрытием"""
        if self.user.email:
            parts = self.user.email.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                if len(username) > 2:
                    visible = username[:2] + '***' + username[-1:]
                else:
                    visible = '***'
                return f"{visible}@{domain}"
        return "Не указан"

    def get_visible_phone(self):
        """Возвращает телефон с частичным скрытием"""
        if self.phone_number:
            if len(self.phone_number) > 7:
                return f"{self.phone_number[:3]}***{self.phone_number[-4:]}"
            return "***" + self.phone_number[-4:]
        return "Не указан"

    def verify_current_password(self, password):
        """Проверяет текущий пароль"""
        return self.user.check_password(password)


# Signals to create profile when user is created


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        # Extract phone from username if it looks like a phone number
        phone = instance.username if (instance.username.startswith(
            '+') or instance.username.replace('+', '').isdigit()) else ''
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'phone_number': phone}
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
