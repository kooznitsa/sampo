include ./env/.env.local

DOCKER_COMPOSE := docker compose -f ./deploy/compose.yml --env-file ./env/.env.$(ENV) --profile
DOCKER_EXEC := docker exec $(APP_NAME)_backend
DOCKER_PROFILE ?= main
MANAGE = poetry run python manage.py

LOCALE ?= 'ru'
TAG ?= 'list'
APP ?= 'restaurant'
MIGRATION_NAME ?= ''
MIGRATION_NUM ?= ''


# -------------- HELP --------------

# Print all commands
.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build                                           to build Docker containers"
	@echo "  checkmigrations                                 to check migrations"
	@echo "  dump                                            to create database dump"
	@echo "  linter                                          to run linter"
	@echo "  load                                            to load fixtures"
	@echo "  migrations                                      to create migration file with a default name"
	@echo "  migrate                                         to apply migrations"
	@echo "  namedmigrations MIGRATION_NAME=<name>           to create migration file with a specific name"
	@echo "  rollback APP=<app_name> MIGRATION_NUM=<number>  to reverse migrations"
	@echo "  rollbacktozero APP=<app_name>                   to rollback to initial migration"
	@echo "  runserver                                       to run Django server"
	@echo "  startapp APP=<app_name>                         to create a Django app"
	@echo "  stop                                            to stop Docker containers"
	@echo "  testall                                         to run all tests"
	@echo "  testapp APP=<app_name> TAG=<tag>                to run app tests with a tag"


# -------------- SETUP --------------

# Set up virtual environment and activate it (python3.12):
# python3.12 -m venv .venv
# source .venv/bin/activate


# Run Django server
.PHONY: runserver
runserver:
	$(MANAGE) runserver


# -------------- DOCKER --------------

# Build containers
.PHONY: build
build:
	$(DOCKER_COMPOSE) $(DOCKER_PROFILE) up -d --build

# Stop containers
.PHONY: stop
stop:
	$(DOCKER_COMPOSE) $(DOCKER_PROFILE) down


# -------------- DJANGO --------------

# Start an app
# Example: make startapp APP=marketplace
.PHONY: startapp
startapp:
	$(MANAGE) startapp $(APP)


# -------------- MIGRATIONS --------------

# Dry-run migrations
.PHONY: checkmigrations
checkmigrations:
	$(MANAGE) makemigrations --check --dry-run

# Create migration file with a default name
.PHONY: migrations
migrations:
	$(MANAGE) makemigrations

# Create migration file with a specific name
# Example: make namedmigrations MIGRATION_NAME=alter_visa_category_origins
.PHONY: namedmigrations
namedmigrations:
	$(MANAGE) makemigrations --name $(MIGRATION_NAME)

# Apply migrations
.PHONY: migrate
migrate:
	$(MANAGE) migrate

# Reverse migrations
# Example: make rollback APP=visa MIGRATION_NUM=0124
.PHONY: rollback
rollback:
	$(MANAGE) migrate $(APP) $(MIGRATION_NUM)


# Delete all migrations
# Example: make rollbacktozero APP=marketplace
.PHONY: rollbacktozero
rollbacktozero:
	$(MANAGE) migrate $(APP) zero


# -------------- LINTER --------------

# Run linter
.PHONY: linter
linter:
	flake8 ./ --ignore="E121,E122,E126,E201,E226,E266,E402,E501,Q000" --exclude=".venv"


# -------------- TEST --------------

# Create database dump (/api/fixtures/db_data.json)
.PHONY: dump
dump:
	python -Xutf8 manage.py dumpdata --natural-foreign --exclude=auth.permission --exclude=contenttypes --exclude=admin.logentry --exclude=auth.group --exclude=auth.user --exclude=sessions.session --exclude=visa.visafree --indent=4 --output=db_data.json --settings=odyssey.settings

# Load fixtures
.PHONY: load
load:
	$(MANAGE) loaddata db_data.json

# Run all tests
.PHONY: testall
testall:
	$(MANAGE) test

# Run app tests with a tag
# Example: make testapp APP=api TAG=detail
.PHONY: testapp
testapp:
	$(MANAGE) test $(APP).tests --tag=$(TAG)
