FROM odoo:17.0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Устанавливаем python-docx для генерации документов
USER root

# Установка зависимостей (postgresql-client для проверки БД в entrypoint)
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*
RUN uv pip install --system python-docx lxml-html-clean

# Копируем кастомный модуль
COPY --chown=odoo:odoo ./ic_urfu_module /mnt/extra-addons/ic_urfu_module

# Копируем entrypoint скрипт
COPY --chown=odoo:odoo ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Возвращаемся к пользователю odoo
USER odoo

# Expose порт (будет переопределён переменной PORT от Render)
EXPOSE 10000

# Используем кастомный entrypoint
ENTRYPOINT ["/entrypoint.sh"]
