from django.core.management.base import BaseCommand
from core.models import AppEntry

class Command(BaseCommand):
    help = "Build lightweight search index for AppEntry"

    def handle(self, *args, **options):
        updated = 0
        for app in AppEntry.objects.all().prefetch_related('tags'):
            tags_text = " ".join(app.tags.values_list('name', flat=True))
            base = f"{app.title} {app.summary or ''} {tags_text}".strip()
            if app.search_text != base:
                app.search_text = base
                app.save(update_fields=['search_text'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Search index built. Updated: {updated}"))
