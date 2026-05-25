FROM odoo:17.0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Устанавливаем python-docx для генерации документов
USER root
# python-docx тянет свежий lxml; Odoo импортирует lxml.html.clean — нужен отдельный пакет (см. lxml 5.2+).
RUN uv pip install --system python-docx lxml-html-clean

# Возвращаемся к пользователю odoo
USER odoo
