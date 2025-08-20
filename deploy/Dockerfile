FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /home/app

WORKDIR /home/app

COPY ../pyproject.toml ../poetry.lock* ./

RUN pip install poetry
# For production:
# RUN poetry install --without dev --no-root
RUN poetry config virtualenvs.create false

COPY . ./

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
