from dotenv import load_dotenv
import environ

from .base import *  # noqa

load_dotenv(BASE_DIR / 'env' / '.env.test')  # noqa

env = environ.Env()
ENV = env.str('ENV')
VERSION = env.str('VERSION')
APP_NAME = env.str('APP_NAME')

SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.str('DEBUG')
ALLOWED_HOSTS = env.list('URLS')

print('⚙️ Using TEST database settings')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.str('POSTGRES_TEST_DB'),
        'USER': env.str('POSTGRES_TEST_USER'),
        'PASSWORD': env.str('POSTGRES_TEST_PASSWORD'),
        'HOST': env.str('POSTGRES_TEST_HOST'),
        'PORT': env.str('POSTGRES_TEST_PORT'),
        'OPTIONS': {
            'sslmode': env.str('DATABASE_SSLMODE', default='disable'),
        },
    },
}

TIME_ZONE = env.str('TZ')


# ELASTICSEARCH

ELASTICSEARCH_DSL_AUTOSYNC = False
