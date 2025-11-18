import factory

from django.contrib.auth.models import User

DEFAULT_PASSWORD = 'superSecurePassword!12'


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', DEFAULT_PASSWORD)
    is_superuser = True
    is_staff = True

    class Meta:
        model = User
        django_get_or_create = ('username',)
