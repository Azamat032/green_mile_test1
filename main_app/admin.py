from django.contrib import admin
from .models import Certificate, CertificateTemplate
from django import forms


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


class CertificateTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        design = cleaned_data.get('design')
        variation = cleaned_data.get('variation')
        if design and variation:
            existing = CertificateTemplate.objects.filter(
                design=design, variation=variation
            ).exclude(id=self.instance.id)
            if existing.exists():
                raise forms.ValidationError(
                    f"A template with design '{design}' and variation '{variation}' already exists. Please choose a different variation."
                )
        return cleaned_data


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    form = CertificateTemplateAdminForm
    list_display = ('name', 'design', 'variation', 'is_active', 'created_at')
    list_filter = ('design', 'is_active')
    search_fields = ('name', 'variation')
    fields = ('design', 'variation', 'name', 'description',
              'background_image', 'is_active')
