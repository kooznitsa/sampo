# Sampo

## Требования

- python3.12
- make

## Переменные окружения

ENV = local | test | staging | prod

- Переменные окружения: /env/.env.$(ENV)
- Специфичные для окружения настройки: /core/settings/$(ENV).py
- Makefile: include ./env/.env.$(ENV)

## Запуск проекта

```bash
git clone https://github.com/kooznitsa/sampo.git
cd sampo
cp env/.env.example env/.env.local
make build
```
