from django.contrib import admin
from .models import Certificate, CertificateTemplate
# Register your models here.


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'certificate_id',
        'customer_name',
        'recipient_name',
        'tree_count',
        'total_amount',
        'currency',
        'status',
        'created_at'
    ]
    list_filter = [
        'status', 'design', 'currency'
    ]

    readonly_fields = [
        'certificate_id',
        'created_at',
        'completed_at',
        'environmental_impact_display'
    ]
    fieldsets = (
        ('Basic_information', {
            "fields": [
                'certificate_id',
                'status',
                'created_at',
                'completed_at'
            ],
        }),
        ('Customer Details', {
            'fields': [
                'recipient_name',
                'certificate_text',
                'signature_text',
                'tree_count',
                'design'
            ]
        }),
        ('Payment Information', {
            'fields': [
                'total_amount',
                'currency',
                'payment_id'
            ]
        }),
        ('Environmental Imapct', {
            'fields': [
                'environmental_impact_display'
            ]
        })
    )

    def environmental_impact_display(self, obj):
        impact = obj.environmental_impact
        return (
            f"CO₂ Absorption: {impact['co2_absorption_per_year']} kg/year | "
            f"Oxygen Production: {impact['oxygen_production_per_year']} kg/year | "
            f"Air for {impact['air_for_people']} people"
        )
    environmental_impact_display.short_description = 'Environmental Impact'


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['design', 'background_image_preview']
    readonly_fields = ['background_image_preview']

    def background_image_preview(self, obj):
        if obj.background_image:
            return f"<img src='{obj.background_image.url}' style='max-height: 200px;' />"
        return "No image"

    background_image_preview.allow_tags = True
    background_image_preview.short_description = "Preview"
