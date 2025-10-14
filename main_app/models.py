# models.py - REMOVE THIS LINE:
# from main_app.models import CertificateTemplate  # ← DELETE THIS LINE

from django.db import models
from django.contrib.auth.models import User
import uuid

DESIGN_CHOICES = [
    ('professional', 'Professional'),
    ('modern', 'Modern'),
    ('elegant', 'Elegant'),
]


class Certificate(models.Model):
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

    certificate_id = models.CharField(
        max_length=50, unique=True, default=uuid.uuid4)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    recipient_name = models.CharField(max_length=100)
    certificate_text = models.TextField(max_length=300, blank=True)
    signature_text = models.CharField(max_length=100, blank=True)
    tree_count = models.PositiveIntegerField(default=1)
    template = models.ForeignKey(
        'CertificateTemplate',  # Using string reference to avoid circular import
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    design = models.CharField(
        max_length=20, choices=DESIGN_CHOICES, default='professional')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='KZT')
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.recipient_name}"

    @property
    def environmental_impact(self):
        return {
            'co2_absorption_per_year': self.tree_count * 22,
            'oxygen_production_per_year': self.tree_count * 16,
            'air_for_people': self.tree_count * 2,
        }


class CertificateTemplate(models.Model):
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
