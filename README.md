# Sampo

## Требования

- python3.12
- make

## Переменные окружения

ENV = local | dev | staging | prod

- Переменные окружения: /env/.env.$(ENV)
- Специфичные для окружения настройки: /core/settings/$(ENV).py
- Makefile: include ./env/.env.$(ENV)

Для прода заменить dev в compose.yml на prod:

```yml
services:
  backend:
    <<: *app-main
    build:
      context: ../
      target: dev
```

## Запуск проекта

```bash
git clone https://github.com/kooznitsa/sampo.git
cd sampo
cp env/.env.example env/.env.local
make build
```

Для установки зависимостей локально:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root
```

## Релиз

```bash
chmod +x release.sh
./release.sh v1.0.0
```
