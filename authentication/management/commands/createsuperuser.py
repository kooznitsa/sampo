import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Creates superuser with default username and password set in .env.${ENV} file.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', default='admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', default='admin')
        try:
            superuser = User.objects.create_superuser(
                username=username,
                password=password,
            )
            superuser.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser with username {username}')
            )
        except IntegrityError:
            raise CommandError(f'Superuser with username {username} already exists.')
        except Exception as e:
            raise CommandError(e)
