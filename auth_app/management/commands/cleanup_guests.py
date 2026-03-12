from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from auth_app.models import CustomUserProfile


class Command(BaseCommand):
    help = "Delete guest users whose last login is older than 24 hours."

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Delete guests older than this many hours (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many guests would be deleted without actually deleting them',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff = timezone.now() - timedelta(hours=hours)

        guests = CustomUserProfile.objects.filter(
            is_guest=True,
            last_login__lt=cutoff,
        )

        count = guests.count()

        if options['dry_run']:
            self.stdout.write(f"Would delete {count} guest user(s) older than {hours} hours.")
            return

        guests.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} guest user(s) older than {hours} hours."))
