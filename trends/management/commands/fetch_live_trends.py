"""
Management command to fetch live trending data from external APIs.
Run: python manage.py fetch_live_trends
     python manage.py fetch_live_trends --source google_trends
     python manage.py fetch_live_trends --source stocks --source news
     python manage.py fetch_live_trends --clear
"""

from django.core.management.base import BaseCommand
from trends.models import Trend
from services.live_data_service import fetch_all_live_trends, FETCHERS


class Command(BaseCommand):
    help = 'Fetch live trending data from external APIs (Google Trends, Stocks, News, YouTube, Music)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            action='append',
            choices=list(FETCHERS.keys()),
            help='Specific source(s) to fetch from. Can be repeated. Default: all sources.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing API-sourced trends before fetching.',
        )

    def handle(self, *args, **options):
        sources = options.get('source') or list(FETCHERS.keys())

        if options['clear']:
            deleted = Trend.objects.exclude(source='manual').delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} API-sourced trends.'))

        self.stdout.write(f'\nFetching from: {", ".join(sources)}\n')

        results = fetch_all_live_trends(sources=sources)

        total_created = 0
        total_updated = 0

        for source_name, trend_list in results.items():
            created = 0
            updated = 0

            for trend_data in trend_list:
                source_id = trend_data.pop('source_id', None)
                if not source_id:
                    continue

                try:
                    obj, was_created = Trend.objects.update_or_create(
                        source_id=source_id,
                        defaults=trend_data,
                    )
                    if was_created:
                        created += 1
                        self.stdout.write(f'  ✓ NEW: {obj.title[:60]}')
                    else:
                        updated += 1
                        self.stdout.write(f'  ↻ UPD: {obj.title[:60]}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Error: {e}'))

            total_created += created
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(
                f'  [{source_name}] {created} created, {updated} updated'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Done. {total_created} new, {total_updated} updated. '
            f'Total in database: {Trend.objects.count()}'
        ))
