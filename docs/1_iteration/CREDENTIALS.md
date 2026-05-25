# 🔐 Как изменить логины и пароли

## ✨ ЕДИНАЯ ТОЧКА ИЗМЕНЕНИЯ

Все логины и пароли хранятся в **ОДНОМ файле**:

```
ic_urfu_module/config/demo_credentials.py
```

## 📝 Инструкция

### 1. Открой файл конфигурации

```bash
# В редакторе
vim ic_urfu_module/config/demo_credentials.py

# Или
nano ic_urfu_module/config/demo_credentials.py
```

### 2. Измени нужные значения

```python
# ============================================
# УЧЕТНЫЕ ДАННЫЕ СТУДЕНТА
# ============================================
STUDENT_LOGIN = "student"          # ← Измени логин
STUDENT_PASSWORD = "student"       # ← Измени пароль
STUDENT_EMAIL = "student@example.com"
STUDENT_NAME = "Иванов Петр Сергеевич"

# ============================================
# УЧЕТНЫЕ ДАННЫЕ ПРЕПОДАВАТЕЛЯ
# ============================================
TEACHER_LOGIN = "teacher"          # ← Измени логин
TEACHER_PASSWORD = "teacher"       # ← Измени пароль
TEACHER_EMAIL = "teacher@example.com"
TEACHER_NAME = "Смирнова Анна Викторовна"
```

### 3. Примени изменения

```bash
# Способ 1: Полная переинициализация (рекомендуется)
make clean      # Удалить старые данные
make init       # Создать заново с новыми паролями

# Способ 2: Только для демо XML (если модуль еще не установлен)
make update-credentials
```

### 4. Готово!

Теперь можешь войти с новыми учетными данными:

```
http://localhost:8069
```

## 🎯 Что происходит автоматически

Когда ты меняешь `demo_credentials.py`, эти данные используются:

✅ В `demo_users.xml` (генерируется автоматически при `make init`)
✅ В `load_demo_data.py` (скрипт загрузки данных)
✅ В выводе `make start` (показывает текущие пароли)
✅ В выводе `make init` (показывает текущие пароли)

**Больше никуда не нужно вносить изменения!**

## 📋 Пример: Смена паролей

```bash
# 1. Открыть файл
vim ic_urfu_module/config/demo_credentials.py

# 2. Изменить пароли
#    STUDENT_PASSWORD = "MySecurePass123"
#    TEACHER_PASSWORD = "TeacherPass456"

# 3. Применить
make clean && make init

# 4. Войти с новыми паролями
#    student / MySecurePass123
#    teacher / TeacherPass456
```

## 🔍 Проверка текущих паролей

Посмотреть текущие пароли без запуска:

```bash
# Способ 1: Посмотреть файл
cat ic_urfu_module/config/demo_credentials.py

# Способ 2: Через Python
python3 -c "import sys; sys.path.insert(0, '.'); from ic_urfu_module.config import demo_credentials as c; print(f'Student: {c.STUDENT_LOGIN} / {c.STUDENT_PASSWORD}'); print(f'Teacher: {c.TEACHER_LOGIN} / {c.TEACHER_PASSWORD}')"

# Способ 3: Через make (если контейнеры запущены)
make start  # Покажет текущие логины/пароли
```

## ⚠️ Важно

- **НЕ коммить** реальные пароли в Git!
- Для production используй сильные пароли
- Этот файл для **demo** окружения

## 🎨 Что еще можно менять

В `demo_credentials.py` также можно изменить:

```python
STUDENT_EMAIL = "новый@email.com"      # Email студента
STUDENT_NAME = "Новое ФИО"             # Имя студента

TEACHER_EMAIL = "преподаватель@email.com"
TEACHER_NAME = "ФИО Преподавателя"
```

После изменения запусти `make clean && make init`.

---

**Все просто!** Один файл → все изменения применяются автоматически 🎉
