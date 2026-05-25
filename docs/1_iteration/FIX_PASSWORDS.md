# 🔧 Fix Passwords Command

## Проблема

При входе в Odoo появляется ошибка **"Wrong login/password"**, хотя используются правильные учетные данные.

## Быстрое решение

```bash
make fix-passwords
```

Эта команда:
1. ✅ Проверит что контейнеры запущены
2. ✅ Обновит пароли в базе данных
3. ✅ Установит пароли `student` / `student` и `teacher` / `teacher`
4. ✅ Покажет подтверждение

## Когда использовать

- После первого запуска проекта, если не можешь войти
- После обновления модуля
- После изменения конфигурации
- Если забыл пароли

## Пример использования

```bash
$ make fix-passwords

==========================================
  Fixing User Passwords
==========================================

🔧 Updating passwords in database...

✓ Student password updated (ID: 9)
✓ Teacher password updated (ID: 10)
✅ Passwords updated successfully!

==========================================
  ✅ Done!
==========================================

🔐 You can now login with:

   Student:  student / student
   Teacher:  teacher / teacher

🌐 URL: http://localhost:8069
```

## Альтернативные способы

### Способ 1: Через скрипт напрямую

```bash
./scripts/fix_passwords.sh
```

### Способ 2: Полная переинициализация

```bash
make clean && make init
```

⚠️ **Внимание:** Это удалит все данные!

### Способ 3: Вручную через Odoo shell

```bash
docker exec -i odoo_app odoo shell -c /etc/odoo/odoo.conf -d odoo --no-http <<'EOF'
student = env['res.users'].search([('login', '=', 'student')], limit=1)
student.write({'password': 'student'})

teacher = env['res.users'].search([('login', '=', 'teacher')], limit=1)
teacher.write({'password': 'teacher'})

env.cr.commit()
EOF
```

## Что делает команда под капотом

1. Проверяет что Docker контейнер `odoo_app` запущен
2. Открывает Odoo shell
3. Ищет пользователей `student` и `teacher` в базе
4. Обновляет их пароли
5. Сохраняет изменения (commit)

## Troubleshooting

### Ошибка: "Odoo container is not running"

Контейнеры не запущены. Запусти их:

```bash
make start
```

### Ошибка: "User not found"

Пользователи не созданы. Запусти инициализацию:

```bash
make init
```

### Всё равно не могу войти

1. Проверь что используешь правильный URL: `http://localhost:8069`
2. Проверь что вводишь логин без пробелов: `student` (не `Student`)
3. Попробуй очистить cookies браузера
4. Попробуй другой браузер
5. Проверь логи: `make logs`

---

**Совет:** Добавь эту команду в закладки - она пригодится! 🔖
