from dotenv import load_dotenv
import environ

from .base import *  # noqa

load_dotenv(BASE_DIR / 'env' / '.env.local')  # noqa

env = environ.Env()
ENV = env.str('ENV')
VERSION = env.str('VERSION')
APP_NAME = env.str('APP_NAME')

SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.str('DEBUG')
ALLOWED_HOSTS = env.list('URLS')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.str('POSTGRES_DB'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
        'HOST': env.str('POSTGRES_HOST'),
        'PORT': env.str('POSTGRES_PORT'),
        'OPTIONS': {
            'sslmode': env.str('DATABASE_SSLMODE', default='disable'),
        },
    }
}

TIME_ZONE = env.str('TZ')
