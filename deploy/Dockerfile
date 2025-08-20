FROM python:3.12 AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /home/app

WORKDIR /home/app

COPY ../pyproject.toml ../poetry.lock* ./

RUN pip install poetry

RUN poetry config virtualenvs.create false

COPY . ./

# Dev stage
FROM base AS dev
RUN poetry install --with dev --no-root

# Prod stage
FROM base AS prod
RUN poetry install --without dev --no-root

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
