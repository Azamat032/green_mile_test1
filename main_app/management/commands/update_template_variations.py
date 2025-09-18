from django.core.management.base import BaseCommand
from main_app.models import CertificateTemplate


class Command(BaseCommand):
    help = 'Update existing CertificateTemplate objects with a variation field'

    def handle(self, *args, **kwargs):
        templates = CertificateTemplate.objects.all()
        for index, template in enumerate(templates, 1):
            if not template.variation:
                template.variation = f'variation-{index}'
                template.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Updated template {template.id} with variation: variation-{index}'
                ))
