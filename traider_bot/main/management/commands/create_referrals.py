from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Referral


class Command(BaseCommand):
    help = 'Create referral objects for existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0

        for user in users:
            if not hasattr(user, 'referral'):
                referral = Referral.objects.create(user=user)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Referral created for user {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'Total {created_count} referral objects created.'))
