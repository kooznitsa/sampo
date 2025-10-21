include ./env/.env.local

DOCKER_COMPOSE := docker compose -f ./deploy/compose.yml --env-file ./env/.env.$(ENV) --profile
DOCKER_EXEC := docker exec $(APP_NAME)_backend
DOCKER_PROFILE ?= main
MANAGE = poetry run python manage.py

LOCALE ?= 'ru'
TAG ?= 'list'
APP ?= restaurant
MIGRATION_NAME ?= ''
MIGRATION_NUM ?= ''
PACKAGE ?= ''
RESTAURANT_URL ?= ''


# -------------- HELP --------------

# Print all commands
.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build                                           to build Docker containers"
	@echo "  checkmigrations                                 to check migrations"
	@echo "  collect_links                                   to collect restaurant links"
	@echo "  createsuperuser                                 to create super user"
	@echo "  dump                                            to create database dump"
	@echo "  linter                                          to run linter"
	@echo "  load                                            to load fixtures"
	@echo "  migrations                                      to create migration file with a default name"
	@echo "  migrate                                         to apply migrations"
	@echo "  mypy                                            to check typing"
	@echo "  namedmigrations MIGRATION_NAME=<name>           to create migration file with a specific name"
	@echo "  poetryadd PACKAGE=<package>                     to add package"
	@echo "  rollback APP=<app_name> MIGRATION_NUM=<number>  to reverse migrations"
	@echo "  rollbacktozero APP=<app_name>                   to rollback to initial migration"
	@echo "  scrape_menu                                     to scrape menu"
	@echo "  scrape_restaurant RESTAURANT_URL=<url>          to scrape restaurant"
	@echo "  startapp APP=<app_name>                         to create a Django app"
	@echo "  stop                                            to stop Docker containers"
	@echo "  testall                                         to run all tests"
	@echo "  testapp APP=<app_name> TAG=<tag>                to run app tests with a tag"



# -------------- SETUP --------------

# For `poetry add` command
# Set up virtual environment and activate it:
# python3.12 -m venv .venv
# source .venv/bin/activate


# -------------- DOCKER --------------

# Build containers
.PHONY: build
build:
	$(DOCKER_COMPOSE) $(DOCKER_PROFILE) up -d --build

# Stop containers
.PHONY: stop
stop:
	$(DOCKER_COMPOSE) $(DOCKER_PROFILE) down

# Enter backend container
.PHONY: entercontainer
entercontainer:
	docker exec -it $(APP_NAME)_backend sh


# -------------- PACKAGES --------------

# Add package
# Example: make poetryadd PACKAGE=mypy
.PHONY: poetryadd
poetryadd:
	$(DOCKER_EXEC) poetry add $(PACKAGE)


# -------------- DJANGO --------------

# Start an app
# Example: make startapp APP=restaurant
.PHONY: startapp
startapp:
	$(MANAGE) startapp $(APP)

# Creates superuser
.PHONY: createsuperuser
createsuperuser:
	$(DOCKER_EXEC) $(MANAGE) createsuperuser --noinput


# -------------- MIGRATIONS --------------

# Dry-run migrations
.PHONY: checkmigrations
checkmigrations:
	$(DOCKER_EXEC) $(MANAGE) makemigrations --check --dry-run --settings=core.settings.$(ENV)

# Create migration file with a default name
.PHONY: migrations
migrations:
	$(DOCKER_EXEC) $(MANAGE) makemigrations --settings=core.settings.$(ENV)

# Create migration file with a specific name
# Example: make namedmigrations MIGRATION_NAME=alter_visa_category_origins
.PHONY: namedmigrations
namedmigrations:
	$(DOCKER_EXEC) $(MANAGE) makemigrations --name $(MIGRATION_NAME) --settings=core.settings.$(ENV)

# Apply migrations
.PHONY: migrate
migrate:
	$(DOCKER_EXEC) $(MANAGE) migrate --settings=core.settings.$(ENV)

# Reverse migrations
# Example: make rollback APP=restaurant MIGRATION_NUM=0124
.PHONY: rollback
rollback:
	$(DOCKER_EXEC) $(MANAGE) migrate $(APP) $(MIGRATION_NUM) --settings=core.settings.$(ENV)

# Delete all migrations
# Example: make rollbacktozero APP=restaurant
.PHONY: rollbacktozero
rollbacktozero:
	$(DOCKER_EXEC) $(MANAGE) migrate $(APP) zero --settings=core.settings.$(ENV)


# -------------- DATABASE --------------

# Create database dump
.PHONY: dump
dump:
	$(DOCKER_EXEC) poetry run python -Xutf8 manage.py dumpdata --natural-foreign --exclude=auth.permission --exclude=contenttypes --exclude=admin.logentry --exclude=auth.group --exclude=auth.user --exclude=sessions.session --output=db_data.json --settings=core.settings.local

# Load database data
.PHONY: load
load:
	$(DOCKER_EXEC) $(MANAGE) loaddata db_data.json


# -------------- LINTER --------------

# Run linter
.PHONY: linter
linter:
	$(DOCKER_EXEC) poetry run flake8 ./ --ignore="E121,E122,E126,E201,E226,E266,E402,E501,Q000" --exclude=".venv"


# Check typing
.PHONY: mypy
mypy:
	$(DOCKER_EXEC) poetry run mypy .

# Check app typing in CI
# Example: make mypyapp-ci; make mypyapp-ci APP=restaurant
.PHONY: mypyapp-ci
mypyapp-ci:
	poetry run mypy $(APP) --no-incremental


# -------------- TEST --------------

# Run migrations for test database
.PHONY: testmigrate
testmigrate:
	export DJANGO_SETTINGS_MODULE=core.settings.test;
	$(DOCKER_EXEC) $(MANAGE) migrate

# Run all tests
.PHONY: testall
testall:
	$(DOCKER_EXEC) $(MANAGE) test --settings=core.settings.test

# Run app tests with a tag
# Example: make testapp APP=restaurant TAG=detail
.PHONY: testapp
testapp:
	$(DOCKER_EXEC) $(MANAGE) test $(APP).tests --tag=$(TAG) --settings=core.settings.test


# -------------- CUSTOM COMMANDS --------------

# Collect restaurant links
.PHONY: collect_links
collect_links:
	$(DOCKER_EXEC) $(MANAGE) collect_links

# Scrape restaurant menu
.PHONY: scrape_menu
scrape_menu:
	$(DOCKER_EXEC) $(MANAGE) scrape_menu

# Scrape restaurant data
# Example: make scrape_restaurant RESTAURANT_URL=https://yandex.ru/maps/org/luchi/186752599757/menu/
.PHONY: scrape_restaurant
scrape_restaurant:
	$(DOCKER_EXEC) $(MANAGE) scrape_restaurant $(RESTAURANT_URL)
