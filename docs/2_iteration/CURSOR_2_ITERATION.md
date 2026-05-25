# Cursor — Итерация 2: Задачи для разработки

> **Контекст проекта:** Odoo 17 модуль `ic_urfu_module`, Python 3.12+, PostgreSQL 17, python-docx.
> Все бизнес-модели живут в `ic_urfu_module/models/ic_urfu.py`.
> Генератор DOCX: `ic_urfu_module/doc_generator/doc_generator.py`.
> Все новые файлы моделей/wizards регистрировать в `ic_urfu_module/__manifest__.py` в секции `data`.

---

## Задача 0 — Подготовка ветки и манифеста

```
Переключись на ветку dev и создай от неё ветку feature/iteration-2.

Открой ic_urfu_module/__manifest__.py и убедись в структуре секций 'data' и 'demo'.
Запомни этот файл — в него нужно будет добавлять ссылки на все новые XML-файлы views и data
в рамках этой итерации.

Проверь, что make init выполняется без ошибок (docker compose up, установка модуля, демо-данные).
```

---

## Задача 1 — Убрать ФИО студента из автогенерации DOCX

### Что нужно сделать

```
Файл: ic_urfu_module/doc_generator/doc_generator.py

1. Найди все места, где в документ вставляются данные студента.
   Ищи по ключевым словам: student_name, fio, full_name, ФИО, student.name,
   а также по вызовам типа plan.student_name, plan.partner_id.name и похожим.

2. Для каждого такого места:
   - Если это ФИО (имя, фамилия, отчество) — замени на строку "___________________"
   - Если это программа, институт, год поступления, направление — оставь как есть

3. Найди метод _prepare_document_data в модели ic.urfu.plan (файл ic_urfu_module/models/ic_urfu.py).
   В словаре данных, который этот метод возвращает, найди ключ со значением ФИО студента
   и замени его значение на пустую строку "" или на "___________________".

4. В методе action_generate_document той же модели найди валидацию, которая проверяет
   заполненность ФИО перед генерацией. Убери эту проверку или сделай поле необязательным.

5. В самом DOCX-документе после таблицы с шапкой добавь строку мелким шрифтом (10pt):
   "* ФИО студента заполняется собственноручно"
   Используй для этого python-docx: paragraph.runs[0].font.size = Pt(10).

6. Проверь: запусти make test-generator и убедись, что DOCX генерируется без ошибок,
   а поле ФИО в документе — пустое с подчёркиванием.
```

---

## Задача 2 — Предзаполнение обязательных дисциплин по направлению

### Шаг 2.1 — Новые модели шаблонов программ

```
Файл: ic_urfu_module/models/ic_urfu.py

Добавь в конец файла две новые модели Odoo ORM:

Модель 1 — ic.urfu.program.template:
  _name = 'ic.urfu.program.template'
  _description = 'Шаблон образовательной программы'
  Поля:
    name: Char, required, string='Название программы' (например "Информационные технологии")
    code: Char, string='Код направления' (например "09.03.01")
    semester_template_ids: One2many на ic.urfu.semester.template, обратное поле program_id

Модель 2 — ic.urfu.semester.template:
  _name = 'ic.urfu.semester.template'
  _description = 'Шаблон семестра для программы'
  Поля:
    program_id: Many2one на ic.urfu.program.template, required, ondelete='cascade'
    semester_number: Integer, required, string='Номер семестра', от 1 до 8
    subject_ids: Many2many на ic.urfu.subject, relation='semester_template_subject_rel',
                 string='Обязательные дисциплины шаблона'

В модель ic.urfu.plan добавь поле:
    program_template_id: Many2one на ic.urfu.program.template,
                         string='Шаблон программы', tracking=True
```

### Шаг 2.2 — Метод применения шаблона

```
Файл: ic_urfu_module/models/ic_urfu.py, класс IndividualPlan (или как называется класс ic.urfu.plan)

Добавь метод action_apply_template(self):

  @api.multi  # или просто def action_apply_template(self): в зависимости от версии Odoo 17
  def action_apply_template(self):
      self.ensure_one()
      if not self.program_template_id:
          raise UserError("Выберите шаблон программы перед применением.")
      
      for sem_tmpl in self.program_template_id.semester_template_ids:
          # Ищем существующий семестр с таким номером в плане
          existing = self.semester_ids.filtered(
              lambda s: s.semester_number == sem_tmpl.semester_number
          )
          if existing:
              sem = existing[0]
              # Добавляем дисциплины из шаблона к обязательным, не дублируя
              new_subjects = sem_tmpl.subject_ids - sem.mandatory_subject_ids
              sem.mandatory_subject_ids = [(4, subj.id) for subj in new_subjects]
          else:
              # Создаём новый семестр
              self.env['ic.urfu.semester'].create({
                  'plan_id': self.id,
                  'semester_number': sem_tmpl.semester_number,
                  'mandatory_subject_ids': [(6, 0, sem_tmpl.subject_ids.ids)],
              })
      
      return {
          'type': 'ir.actions.client',
          'tag': 'display_notification',
          'params': {
              'message': f'Шаблон "{self.program_template_id.name}" применён.',
              'type': 'success',
          }
      }

Добавь onchange на поле program_template_id:

  @api.onchange('program_template_id')
  def _onchange_program_template(self):
      if self.program_template_id and not self.semester_ids:
          # Автоматически спрашиваем применить шаблон только если семестров ещё нет
          return {
              'warning': {
                  'title': 'Шаблон выбран',
                  'message': 'Нажмите "Применить шаблон" чтобы предзаполнить обязательные дисциплины.'
              }
          }
```

### Шаг 2.3 — Views и демо-данные

```
Создай файл ic_urfu_module/views/program_template_views.xml:

  <odoo>
    <!-- Форма шаблона программы -->
    <record id="view_program_template_form" model="ir.ui.view">
      <field name="name">ic.urfu.program.template.form</field>
      <field name="model">ic.urfu.program.template</field>
      <field name="arch" type="xml">
        <form>
          <sheet>
            <group>
              <field name="name"/>
              <field name="code"/>
            </group>
            <notebook>
              <page string="Семестры">
                <field name="semester_template_ids">
                  <tree editable="bottom">
                    <field name="semester_number"/>
                    <field name="subject_ids" widget="many2many_tags"/>
                  </tree>
                </field>
              </page>
            </notebook>
          </sheet>
        </form>
      </field>
    </record>

    <!-- Tree list -->
    <record id="view_program_template_tree" model="ir.ui.view">
      <field name="name">ic.urfu.program.template.tree</field>
      <field name="model">ic.urfu.program.template</field>
      <field name="arch" type="xml">
        <tree>
          <field name="name"/>
          <field name="code"/>
        </tree>
      </field>
    </record>

    <!-- Action -->
    <record id="action_program_template" model="ir.actions.act_window">
      <field name="name">Шаблоны программ</field>
      <field name="res_model">ic.urfu.program.template</field>
      <field name="view_mode">tree,form</field>
    </record>

    <!-- Пункт меню в Настройках -->
    <menuitem id="menu_program_templates"
              name="Шаблоны программ"
              parent="СЮДА_ВСТАВЬ_ID_РОДИТЕЛЬСКОГО_МЕНЮ_НАСТРОЕК"
              action="action_program_template"
              sequence="20"/>
  </odoo>

ВАЖНО: замени СЮДА_ВСТАВЬ_ID_РОДИТЕЛЬСКОГО_МЕНЮ_НАСТРОЕК на реальный id родительского пункта меню.
Найди его в ic_urfu_module/views/ — ищи menuitem с name содержащим "Настройки" или "Configuration".

На форме ic.urfu.plan добавь:
  - поле program_template_id (Many2one, видно только в draft)
  - кнопку <button name="action_apply_template" string="Применить шаблон" type="object"
                    attrs="{'invisible': [('state', '!=', 'draft')]}"/>

Создай файл ic_urfu_module/data/program_template_data.xml с 2 примерами:
  - Программа "Программная инженерия" код 09.03.04 с дисциплинами на семестры 1-4
  - Программа "Прикладная математика и информатика" код 01.03.02 с дисциплинами на семестры 1-4
  Используй только те subject_ids, которые уже есть в demo-данных модуля.
  Ссылайся на них через <ref id="..."/> — найди их id в ic_urfu_module/demo/*.xml.

Добавь оба новых XML в __manifest__.py:
  'data': [..., 'views/program_template_views.xml', 'data/program_template_data.xml']
```

---

## Задача 3 — Обязательный комментарий при возврате плана

### Шаг 3.1 — Wizard модель

```
Создай новый файл ic_urfu_module/wizards/__init__.py если не существует.
Создай ic_urfu_module/wizards/reject_plan_wizard.py:

  from odoo import models, fields, api
  from odoo.exceptions import UserError

  class RejectPlanWizard(models.TransientModel):
      _name = 'ic.urfu.reject.wizard'
      _description = 'Wizard возврата плана на доработку'

      plan_id = fields.Many2one('ic.urfu.plan', string='План', required=True, readonly=True)
      comment = fields.Text(string='Причина возврата', required=True,
                            help='Обязательно укажите, что именно нужно исправить студенту')

      def action_confirm_reject(self):
          self.ensure_one()
          plan = self.plan_id
          plan.write({
              'state': 'rejected',
              'rejection_comment': self.comment,
          })
          plan.message_post(
              body=f'<b>План возвращён на доработку.</b><br/>Комментарий проверяющего: {self.comment}',
              subtype_xmlid='mail.mt_comment',
          )
          return {'type': 'ir.actions.act_window_close'}
```

### Шаг 3.2 — Изменения в модели ic.urfu.plan

```
Файл: ic_urfu_module/models/ic_urfu.py, модель ic.urfu.plan

1. Добавь поле:
   rejection_comment = fields.Text(
       string='Комментарий проверяющего',
       readonly=True,
       tracking=True,
   )

2. Найди метод action_reject (или как он называется — ищи по 'rejected' или 'reject').
   Замени его реализацию на открытие wizard:

   def action_reject(self):
       self.ensure_one()
       return {
           'type': 'ir.actions.act_window',
           'name': 'Возврат плана на доработку',
           'res_model': 'ic.urfu.reject.wizard',
           'view_mode': 'form',
           'target': 'new',
           'context': {'default_plan_id': self.id},
       }
```

### Шаг 3.3 — View wizard и отображение комментария на форме плана

```
Создай ic_urfu_module/views/reject_plan_wizard_views.xml:

  <odoo>
    <record id="view_reject_plan_wizard_form" model="ir.ui.view">
      <field name="name">ic.urfu.reject.wizard.form</field>
      <field name="model">ic.urfu.reject.wizard</field>
      <field name="arch" type="xml">
        <form string="Возврат плана на доработку">
          <sheet>
            <group>
              <field name="plan_id" readonly="1"/>
            </group>
            <group>
              <field name="comment"
                     placeholder="Опишите подробно, что нужно исправить студенту..."
                     attrs="{'required': [('id', '!=', False)]}"/>
            </group>
          </sheet>
          <footer>
            <button name="action_confirm_reject" string="Вернуть на доработку"
                    type="object" class="btn-danger"/>
            <button string="Отмена" class="btn-secondary" special="cancel"/>
          </footer>
        </form>
      </field>
    </record>
  </odoo>

На форме ic.urfu.plan добавь отображение комментария:
  <field name="rejection_comment"
         attrs="{'invisible': [('rejection_comment', '=', False)]}"
         widget="html" readonly="1"
         class="alert alert-warning"/>

Добавь в ic_urfu_module/__init__.py импорт wizards:
  from . import wizards

Добавь в ic_urfu_module/wizards/__init__.py:
  from . import reject_plan_wizard

Добавь в __manifest__.py:
  'data': [..., 'views/reject_plan_wizard_views.xml']
```

---

## Задача 4 — Валидация ЗЕТ и нагрузки

### Шаг 4.1 — Настройки лимитов

```
Файл: ic_urfu_module/models/ic_urfu.py, класс IcUrfuConfigSettings (или ic.urfu.config.settings)

Добавь поля конфигурации (если используется ir.config_parameter — добавь аналогично уже существующим):

  min_semester_zet = fields.Integer(
      string='Мин. ЗЕТ за семестр', default=25,
      config_parameter='ic_urfu.min_semester_zet'
  )
  max_semester_zet = fields.Integer(
      string='Макс. ЗЕТ за семестр', default=35,
      config_parameter='ic_urfu.max_semester_zet'
  )
  total_plan_zet = fields.Integer(
      string='Норма ЗЕТ за весь план', default=240,
      config_parameter='ic_urfu.total_plan_zet'
  )
  max_hours_per_week = fields.Integer(
      string='Макс. ауд. часов в неделю', default=36,
      config_parameter='ic_urfu.max_hours_per_week'
  )

Добавь эти поля на форму настроек в соответствующем views XML-файле.
```

### Шаг 4.2 — Вычисляемые поля ЗЕТ

```
Файл: ic_urfu_module/models/ic_urfu.py

В модели ic.urfu.semester добавь вычисляемое поле:

  zet_total = fields.Float(
      string='Итого ЗЕТ', compute='_compute_zet_total', store=True
  )

  @api.depends('mandatory_subject_ids.zet', 'elective_subject_ids.zet')
  def _compute_zet_total(self):
      for sem in self:
          zet = sum(sem.mandatory_subject_ids.mapped('zet'))
          zet += sum(sem.elective_subject_ids.mapped('zet'))
          sem.zet_total = zet

  ВАЖНО: проверь реальное название поля ЗЕТ в модели ic.urfu.subject — ищи по 'zet', 'credits',
  'credit_hours' или похожему. Используй именно его.

В модели ic.urfu.plan добавь:

  total_zet = fields.Float(
      string='Всего ЗЕТ по плану', compute='_compute_total_zet', store=True
  )

  @api.depends('semester_ids.zet_total')
  def _compute_total_zet(self):
      for plan in self:
          plan.total_zet = sum(plan.semester_ids.mapped('zet_total'))
```

### Шаг 4.3 — Валидации при отправке плана

```
Файл: ic_urfu_module/models/ic_urfu.py, в метод action_submit (или как называется метод
перевода плана из draft в submitted — ищи по 'submitted' или 'submit')

Добавь вызов нового метода _validate_zet_constraints(self) перед изменением state.

Создай метод _validate_zet_constraints(self):

  def _validate_zet_constraints(self):
      self.ensure_one()
      ICP = self.env['ir.config_parameter'].sudo()
      min_zet = int(ICP.get_param('ic_urfu.min_semester_zet', 25))
      max_zet = int(ICP.get_param('ic_urfu.max_semester_zet', 35))
      total_norm = int(ICP.get_param('ic_urfu.total_plan_zet', 240))
      max_weekly = int(ICP.get_param('ic_urfu.max_hours_per_week', 36))

      errors = []
      warnings = []

      for sem in self.semester_ids:
          # Проверка ЗЕТ за семестр
          if sem.zet_total < min_zet or sem.zet_total > max_zet:
              errors.append(
                  f'Семестр {sem.semester_number}: {sem.zet_total} ЗЕТ '
                  f'(допустимо {min_zet}–{max_zet})'
              )
          # Проверка аудиторной нагрузки в неделю
          # Ищи поле с часами в модели ic.urfu.subject: hours, academic_hours, contact_hours
          total_hours = sum(
              (sem.mandatory_subject_ids + sem.elective_subject_ids).mapped('hours')
          )
          weekly = total_hours / 18  # 18 недель в семестре
          if weekly > max_weekly:
              warnings.append(
                  f'Семестр {sem.semester_number}: ~{weekly:.1f} ч/нед '
                  f'(рекомендуется не более {max_weekly})'
              )

      # Проверка суммарных ЗЕТ
      if abs(self.total_zet - total_norm) > 5:
          warnings.append(
              f'Итого по плану: {self.total_zet} ЗЕТ (норма {total_norm} ЗЕТ)'
          )

      if errors:
          raise ValidationError(
              'Обнаружены ошибки нагрузки:\n' + '\n'.join(f'• {e}' for e in errors)
          )
      if warnings:
          # Предупреждение — не блокирует отправку, но показывается студенту
          return {
              'warning': {
                  'title': 'Предупреждение о нагрузке',
                  'message': '\n'.join(warnings)
              }
          }

ВАЖНО: проверь реальное название поля часов в ic.urfu.subject и используй именно его.
Импортируй ValidationError если ещё не импортирован: from odoo.exceptions import ValidationError, UserError
```

### Шаг 4.4 — Отображение ЗЕТ в интерфейсе

```
В view-файле формы ic.urfu.semester добавь внизу формы:
  <group>
    <field name="zet_total" readonly="1" widget="float" string="Итого ЗЕТ в семестре"/>
  </group>

В view-файле формы ic.urfu.plan добавь stat button или поле:
  <field name="total_zet" readonly="1" string="Всего ЗЕТ по плану"/>
```

---

## Задача 5 — Предзаполнение модульных спецкурсов на следующий семестр

```
Файл: ic_urfu_module/models/ic_urfu.py

Шаг 5.1 — В модели ic.urfu.subject добавь поля:

  is_modular = fields.Boolean(string='Модульный спецкурс', default=False)
  next_module_id = fields.Many2one(
      'ic.urfu.subject',
      string='Следующая часть модуля',
      domain=[('is_modular', '=', True)],
  )

Шаг 5.2 — В модели ic.urfu.plan добавь метод action_suggest_next_modules(self):

  def action_suggest_next_modules(self):
      self.ensure_one()
      suggested = []
      for sem in self.semester_ids:
          modular_subjects = (
              sem.mandatory_subject_ids + sem.elective_subject_ids
          ).filtered(lambda s: s.is_modular and s.next_module_id)

          if not modular_subjects:
              continue

          next_sem = self.semester_ids.filtered(
              lambda s: s.semester_number == sem.semester_number + 1
          )
          if not next_sem:
              continue

          next_sem = next_sem[0]
          for subj in modular_subjects:
              next_subj = subj.next_module_id
              already_there = next_subj in (
                  next_sem.mandatory_subject_ids + next_sem.elective_subject_ids
              )
              if not already_there:
                  next_sem.elective_subject_ids = [(4, next_subj.id)]
                  suggested.append(
                      f'Сем. {next_sem.semester_number}: добавлен «{next_subj.name}»'
                  )

      if suggested:
          message = 'Предложены продолжения модулей:\n' + '\n'.join(f'• {s}' for s in suggested)
      else:
          message = 'Не найдено модульных спецкурсов с продолжением в следующих семестрах.'

      return {
          'type': 'ir.actions.client',
          'tag': 'display_notification',
          'params': {'message': message, 'type': 'info', 'sticky': True},
      }

Шаг 5.3 — В view-файле формы ic.urfu.plan добавь кнопку:
  <button name="action_suggest_next_modules"
          string="Предложить продолжения модулей"
          type="object"
          attrs="{'invisible': [('state', '!=', 'draft')]}"
          icon="fa-magic"/>

Шаг 5.4 — В view-файле формы ic.urfu.subject добавь поля:
  <field name="is_modular"/>
  <field name="next_module_id" attrs="{'invisible': [('is_modular', '=', False)]}"/>

Шаг 5.5 — В демо-данных (demo/*.xml) добавь 2-3 примера дисциплин с is_modular=True
и заполненным next_module_id для демонстрации фичи.
```

---

## Задача 6 — Деплой на сервер

### Шаг 6.1 — Проверка и починка корневого Dockerfile

```
Открой корневой Dockerfile (в корне репозитория, не local-env/Dockerfile).

Убедись, что он содержит примерно следующее (исправь если нужно):

  FROM odoo:17.0

  USER root

  # Системные зависимости
  RUN apt-get update && apt-get install -y \
      postgresql-client \
      && rm -rf /var/lib/apt/lists/*

  # Python-зависимости
  RUN pip install --no-cache-dir python-docx

  # Копирование модуля
  COPY ic_urfu_module /mnt/extra-addons/ic_urfu_module

  # entrypoint (должен существовать в репо!)
  COPY scripts/entrypoint.sh /entrypoint.sh
  RUN chmod +x /entrypoint.sh

  USER odoo

  ENTRYPOINT ["/entrypoint.sh"]
  CMD ["odoo"]

Если файл scripts/entrypoint.sh не существует — создай его:

  #!/bin/bash
  set -e
  # Запускаем odoo с нашим аддоном
  exec odoo \
    --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
    "$@"

Сделай chmod +x scripts/entrypoint.sh.
```

### Шаг 6.2 — Render.com (основной вариант)

```
Открой render.yaml. Убедись, что:

1. В секции web-сервиса есть переменные окружения:
   - DB_HOST: из managed PostgreSQL
   - DB_USER: из managed PostgreSQL
   - DB_PASSWORD: из managed PostgreSQL (секрет)
   - DB_NAME: имя базы
   - ODOO_ADMIN_PASSWD: пароль мастера Odoo (секрет)

2. healthCheckPath: /web/database/manager

3. В DEPLOY.md добавь раздел "Итерация 2 — ручные шаги после деплоя":
   - Зайти в /web/database/manager
   - Создать базу данных с демо-данными
   - Зайти в Apps → Update Apps List
   - Найти "IC UrFU Module" → Update (если уже установлен) или Install
   - Проверить Настройки → Шаблоны программ — должны быть предзаполненные программы
```

### Шаг 6.3 — Альтернатива: docker-compose для VPS

```
Создай в корне docker-compose.prod.yml:

  version: '3.8'

  services:
    db:
      image: postgres:17
      restart: always
      environment:
        POSTGRES_DB: ${POSTGRES_DB:-odoo}
        POSTGRES_USER: ${POSTGRES_USER:-odoo}
        POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      volumes:
        - postgres_data:/var/lib/postgresql/data

    odoo:
      build:
        context: .
        dockerfile: Dockerfile
      restart: always
      depends_on:
        - db
      ports:
        - "8069:8069"
      environment:
        HOST: db
        USER: ${POSTGRES_USER:-odoo}
        PASSWORD: ${POSTGRES_PASSWORD}
      volumes:
        - odoo_filestore:/var/lib/odoo

    nginx:
      image: nginx:alpine
      restart: always
      depends_on:
        - odoo
      ports:
        - "80:80"
        - "443:443"
      volumes:
        - ./nginx/odoo.conf:/etc/nginx/conf.d/default.conf:ro

  volumes:
    postgres_data:
    odoo_filestore:

Создай nginx/odoo.conf:

  server {
      listen 80;
      client_max_body_size 50m;
      gzip on;
      gzip_types text/plain application/json application/javascript text/css;

      location / {
          proxy_pass http://odoo:8069;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_read_timeout 720s;
          proxy_connect_timeout 720s;
      }

      location /longpolling {
          proxy_pass http://odoo:8072;
      }
  }

Создай .env.prod.example:
  POSTGRES_DB=odoo_prod
  POSTGRES_USER=odoo
  POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD

Добавь в Makefile цели:
  deploy-prod:
      docker compose -f docker-compose.prod.yml up -d --build

  deploy-prod-logs:
      docker compose -f docker-compose.prod.yml logs -f odoo
```

---

## Чеклист: что добавить в `__manifest__.py`

```
После выполнения всех задач убедись, что в ic_urfu_module/__manifest__.py
в секции 'data' присутствуют (в правильном порядке — сначала security, потом views, потом data):

  'security/ic_urfu_security.xml',           # уже есть
  ...все существующие views...               # уже есть
  'views/program_template_views.xml',        # НОВОЕ — Задача 2
  'views/reject_plan_wizard_views.xml',      # НОВОЕ — Задача 3
  'data/program_template_data.xml',          # НОВОЕ — Задача 2

И в секции 'installable': True, 'application': True — должны быть уже.
Версию модуля в 'version' обнови на '17.0.2.0.0'.

В ic_urfu_module/__init__.py убедись, что импортируется папка wizards:
  from . import models
  from . import wizards   # ДОБАВИТЬ если нет
```

---

## Порядок выполнения задач

```
0 (подготовка) → 1 (DOCX) → 3 (wizard reject) → 4.1+4.2 (поля ЗЕТ) →
4.3+4.4 (валидации ЗЕТ в UI) → 2 (шаблоны программ) → 5 (модули) → 6 (деплой)

После каждой задачи:
  make upgrade-module   # применить изменения в работающем Odoo
  make logs             # убедиться, что нет ошибок при старте модуля
```