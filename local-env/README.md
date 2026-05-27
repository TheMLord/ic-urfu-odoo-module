# Local Development Environment

Эта папка содержит конфигурацию Docker для локальной разработки с Odoo 17.0 и PostgreSQL 17.

## Файлы

- **docker-compose.yml** - Конфигурация Docker Compose (Odoo + PostgreSQL)
- **Dockerfile** - Кастомный образ Odoo с python-docx
- **odoo.conf** - Конфигурация Odoo сервера
- **reset_all_passwords.sh** - Скрипт для сброса паролей пользователей

## Быстрый старт

```bash
# Запустить окружение
docker-compose up -d

# Остановить окружение
docker-compose down

# Остановить и удалить volumes (полная очистка)
docker-compose down -v
```

## Доступ

- **Odoo**: http://localhost:8079
- **PostgreSQL**: localhost:2345
- **База данных**: `odoo` (как в `make init` / `scripts/init.sh`)

## Учетные данные

### Odoo (база: odoo)
- **Admin**: admin / admin
- **Студент**: student / student
- **Преподаватель**: teacher / teacher

### PostgreSQL
- **Пользователь**: odoo
- **Пароль**: odoo

## Сброс паролей

Если забыли пароли пользователей:

```bash
./reset_all_passwords.sh
```

## Логи

```bash
# Просмотр логов Odoo
docker logs -f odoo_app

# Просмотр логов PostgreSQL
docker logs -f odoo_db
```

## Обновление модуля

После изменения кода модуля:

```bash
docker exec odoo_app odoo -c /etc/odoo/odoo.conf -d odoo -u ic_urfu_module --stop-after-init
docker restart odoo_app
```