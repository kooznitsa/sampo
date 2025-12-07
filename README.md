# Sampo: проект по поиску ресторанов и еды в Санкт-Петербурге

Сампо — в карельском народном эпосе волшебная мельница, обладающая магической силой и являющаяся источником счастья, благополучия и изобилия.

## Используемые инструменты

<img src="https://img.shields.io/badge/Python-800000?style=for-the-badge&logo=python&logoColor=white"/> <img src="https://img.shields.io/badge/Django-A52A2A?style=for-the-badge&logo=django&logoColor=white"/> <img src="https://img.shields.io/badge/DRF-A52A2A?style=for-the-badge"/> <img src="https://img.shields.io/badge/PostgreSQL-A0522D?style=for-the-badge&logo=PostgreSQL&logoColor=white"/> <img src="https://img.shields.io/badge/NGINX-BDB76B?style=for-the-badge&logo=NGINX&logoColor=white"/>  <img src="https://img.shields.io/badge/Docker-9a7b4d?style=for-the-badge&logo=Docker&logoColor=white"/> <img src="https://img.shields.io/badge/Elasticsearch-9a7b4d?style=for-the-badge&logo=Elasticsearch&logoColor=white"/>

## API

Документация: http://164.92.220.87:1337/api/v1/swagger/

Без авторизации доступны GET-запросы.

## Админка

Админка: http://164.92.220.87:1337/admin/

Доступ в админку в режиме просмотра:

- логин: guest
- пароль: sampopass

## Требования для установки

- git
- Docker, Docker Compose
- make

## Переменные окружения

ENV = local | test | prod

- Переменные окружения: /env/.env.$(ENV)
- Специфичные для окружения настройки: /core/settings/$(ENV).py

## Команды

### Запуск проекта

Для ENV=local:

```bash
# Клонировать проект
git clone https://github.com/kooznitsa/sampo.git sampo

# Создать файлы окружения и поменять нужные переменные
cd sampo
cp env/.env.local.example env/.env.local
cp env/.env.test.example env/.env.test

# Запустить контейнеры Docker
make build

# После наполнения базы данных: создать индексы Elasticsearch
make elastic
```

Для ENV=prod:

```bash
# Клонировать проект
git clone https://github.com/kooznitsa/sampo.git sampo

# Создать файлы окружения и поменять нужные переменные
cd sampo
cp env/.env.prod.example env/.env.prod
cp env/.env.test.example env/.env.test

# Запустить контейнеры Docker
make build ENV=prod

# После наполнения базы данных: создать индексы Elasticsearch
make elastic ENV=prod
```

### Релиз

```bash
git checkout dev
git pull

chmod +x release.sh
./release.sh v1.0.0  # изменить версию

git checkout dev
git merge main
```

## Структура базы данных (основные таблицы)

![Диаграмма базы данных](./db_diagram.png)
