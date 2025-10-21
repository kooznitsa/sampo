# Sampo: проект по поиску ресторанов и еды в Санкт-Петербурге

![Static Badge](https://img.shields.io/badge/development-ongoing-red)

Сампо — в карельском народном эпосе волшебный предмет, обладающий магической силой и являющийся источником счастья, благополучия и изобилия.

## Требования

- python3.12
- make

## Используемые инструменты

<img src="https://img.shields.io/badge/Python-800000?style=for-the-badge&logo=python&logoColor=white"/> <img src="https://img.shields.io/badge/Django-A52A2A?style=for-the-badge&logo=django&logoColor=white"/> <img src="https://img.shields.io/badge/DRF-A52A2A?style=for-the-badge"/> <img src="https://img.shields.io/badge/PostgreSQL-A0522D?style=for-the-badge&logo=PostgreSQL&logoColor=white"/> <img src="https://img.shields.io/badge/NGINX-BDB76B?style=for-the-badge&logo=NGINX&logoColor=white"/>  <img src="https://img.shields.io/badge/Docker-9a7b4d?style=for-the-badge&logo=Docker&logoColor=white"/> <img src="https://img.shields.io/badge/Elasticsearch-9a7b4d?style=for-the-badge&logo=Elasticsearch&logoColor=white"/>

## Переменные окружения

ENV = local | test | dev | staging | prod

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

## Команды

### Запуск проекта

```bash
git clone https://github.com/kooznitsa/sampo.git
cd sampo
cp env/.env.local.example env/.env.local
cp env/.env.test.example env/.env.test
make build
```

### Установка зависимостей локально

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root
```

### Релиз

```bash
chmod +x release.sh
./release.sh v1.0.0  # изменить версию
```

## Структура базы данных (основные таблицы)

![Диаграмма базы данных](https://raw.githubusercontent.com/kooznitsa/sampo/refs/heads/main/db_diagram.png)
