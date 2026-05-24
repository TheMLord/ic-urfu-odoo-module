"""Индивидуальный учебный план магистранта.

Главная агрегатная модель: workflow draft→submitted→approved/rejected→generated,
валидация ЗЕТ-нагрузки, применение шаблона программы, сводка плана и генерация DOCX.
"""

import base64
from pathlib import Path
import tempfile
from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import constants
from ._helpers import _config_param_truthy, _expected_zet_from_hours

try:
    from ..doc_generator import create_urfu_plan
except ImportError:
    create_urfu_plan = None


class IndividualPlan(models.Model):
    """Individual Education Plan model for master's students.

    Manages the complete workflow for creating and approving individual education plans.
    Includes student information, program details, semester planning, and document generation.

    Workflow states:
        draft: Initial state, editable by student
        submitted: Sent for teacher review
        approved: Approved by teacher, ready for document generation
        rejected: Rejected by teacher with comments, returned to draft
        generated: Final document has been generated

    Key features:
        - Role-based access (Student can create/edit, Teacher can approve/reject)
        - Semester and subject planning
        - Document generation in DOCX format following UrFU template
        - Notification system via Odoo messaging
    """

    _name = "ic.urfu.plan"
    _description = "Individual Education Plan"
    _inherit: ClassVar[list[str]] = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Основная информация
    name = fields.Char("Название", compute="_compute_name", store=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Черновик"),
            ("submitted", "На проверке"),
            ("approved", "Одобрено"),
            ("rejected", "Отклонено"),
            ("generated", "Документ создан"),
        ],
        string="Статус",
        default="draft",
        tracking=True,
    )

    # Роли и ответственные
    student_id = fields.Many2one(
        "res.users",
        string="Студент",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        readonly=True,
    )
    teacher_id = fields.Many2one(
        "res.users",
        string="Преподаватель",
        tracking=True,
        domain="[('groups_id', 'in', %(ic_urfu_module.group_ic_urfu_teacher)d)]",
    )
    teacher_comment = fields.Text("Комментарий преподавателя", tracking=True)
    rejection_comment = fields.Text(
        "Комментарий проверяющего",
        readonly=True,
        tracking=True,
        help="Причина возврата плана на доработку (заполняется при отклонении).",
    )

    # Информация о студенте
    student_name = fields.Char("ФИО студента (полное)", required=False, tracking=True)
    student_short_name = fields.Char("ФИО студента (короткое)", compute="_compute_short_name", store=True)

    # Информация об обучении
    institute = fields.Char("Институт", required=True)
    department = fields.Char("Кафедра/Департамент", required=True)
    specialty_code = fields.Char("Направление подготовки", required=True)
    program = fields.Char("Образовательная программа", required=True)

    # Научная деятельность
    supervisor = fields.Char("Научный руководитель")
    research_area = fields.Text("Направление научно-исследовательской деятельности")
    thesis_topic = fields.Text("Тема выпускной квалификационной работы")
    deadline = fields.Char("Срок предоставления ВКР к защите", default="Май 2027")

    # Руководство
    rop_name = fields.Char("Руководитель образовательной программы (РОП)", required=True)
    year = fields.Char("Год", required=True, default="2025")

    # Семестры
    semester_ids = fields.One2many("ic.urfu.semester", "plan_id", string="Семестры")

    total_zet = fields.Float(
        string="Всего ЗЕТ по плану",
        compute="_compute_total_zet",
        store=True,
    )

    program_template_id = fields.Many2one(
        "ic.urfu.program.template",
        string="Шаблон программы",
        tracking=True,
    )

    plan_summary_html = fields.Html(
        string="Сводная таблица",
        compute="_compute_plan_summary_html",
        sanitize=False,
        help="HTML-сводка плана по семестрам: дисциплины, часы, ЗЕТ, итоги.",
    )

    # Генерация документа
    document_file = fields.Binary("Сгенерированный документ", attachment=True)
    document_filename = fields.Char("Имя файла")

    @api.depends("semester_ids.zet_total")
    def _compute_total_zet(self):
        for plan in self:
            plan.total_zet = sum(plan.semester_ids.mapped("zet_total"))

    @api.depends(
        "semester_ids.number",
        "semester_ids.academic_year",
        "semester_ids.mandatory_subject_ids",
        "semester_ids.elective_subject_ids",
        "semester_ids.zet_total",
        "total_zet",
    )
    def _compute_plan_summary_html(self):
        """Сводка плана: рендер через QWeb-шаблон ic_urfu_module.plan_summary."""
        qweb = self.env["ir.qweb"].sudo()
        for plan in self:
            # ir.qweb._render возвращает уже-экранированный markupsafe.Markup, доп. обёртка не нужна.
            plan.plan_summary_html = qweb._render(  # noqa: SLF001 — публичный Odoo API для рендера QWeb
                "ic_urfu_module.plan_summary",
                {"doc": plan, "control_map": constants.CONTROL_FORM_MAPPING},
            )

    @api.depends("student_name", "program")
    def _compute_name(self):
        """Compute plan display name.

        Generates a human-readable name using student's full name.
        Falls back to "Новый план" if student name is not set.
        """
        for record in self:
            if record.student_name:
                record.name = f"План {record.student_name}"
            else:
                record.name = "Новый план"

    @api.depends("student_name")
    def _compute_short_name(self):
        """Generate short name from full student name.

        Converts "Фамилия Имя Отчество" to "И.О. Фамилия" format.
        If the name has fewer than 3 parts, returns the full name unchanged.

        Example:
            "Иванов Петр Сергеевич" → "П.С. Иванов"
        """
        for record in self:
            if record.student_name:
                parts = record.student_name.split()
                if len(parts) >= 3:
                    # Фамилия И.О.
                    record.student_short_name = f"{parts[1][0]}.{parts[2][0]}. {parts[0]}"
                else:
                    record.student_short_name = record.student_name
            else:
                record.student_short_name = ""

    @api.onchange("program_template_id")
    def _onchange_program_template(self):
        if self.program_template_id and not self.semester_ids:
            return {
                "warning": {
                    "title": "Шаблон выбран",
                    "message": 'Нажмите "Применить шаблон" чтобы предзаполнить обязательные дисциплины.',
                },
            }
        return None

    def _program_template_defines_zet_limits(self, tmpl):
        if not tmpl:
            return False
        if (tmpl.min_total_zet or 0) > 0:
            return True
        return any((st.min_zet or 0) > 0 for st in tmpl.semester_template_ids)

    def _zet_semester_line_errors(
        self,
        sem,
        tmpl,
        use_template_zet: bool,
        min_zet_global: int,
        max_zet_global: int,
    ) -> list[str]:
        """Проверка суммы ЗЕТ в семестре: пустые семестры, максимум, минимум (шаблон или глобальный)."""
        errors: list[str] = []
        sn = sem.number
        line = sem.mandatory_subject_ids | sem.elective_subject_ids
        if not line:
            errors.append(f"Семестр {sn}: добавьте хотя бы одну дисциплину.")
            return errors

        zet_val = sem.zet_total

        if zet_val > max_zet_global:
            errors.append(
                f"Семестр {sn}: {zet_val:g} ЗЕТ — больше допустимого максимума {max_zet_global} ЗЕТ за семестр.",
            )

        if tmpl:
            sem_tmpl = tmpl.semester_template_ids.filtered(lambda t, n=sn: t.semester_number == n)[:1]
        else:
            sem_tmpl = self.env["ic.urfu.semester.template"].browse()
        min_template = int(sem_tmpl.min_zet or 0) if sem_tmpl else 0

        min_need = min_template if use_template_zet and min_template > 0 else min_zet_global

        if zet_val < min_need:
            if use_template_zet and min_template > 0:
                errors.append(
                    f"Семестр {sn}: {zet_val:g} ЗЕТ; по программе «{tmpl.name}» в этом семестре "
                    f"нужно не менее {min_need} ЗЕТ.",
                )
            else:
                errors.append(
                    f"Семестр {sn}: {zet_val:g} ЗЕТ (требуется не менее {min_need}, "
                    f"не больше {max_zet_global}).",
                )
        return errors

    def _zet_hour_consistency_errors(self) -> list[str]:
        """Согласованность полей ауд. часов и ЗЕТ у дисциплин с нормой из настроек."""
        self.ensure_one()
        if not _config_param_truthy(self.env, "ic_urfu.enforce_hours_zet", True):
            return []
        icp = self.env["ir.config_parameter"].sudo()
        hpp = int(icp.get_param("ic_urfu.hours_per_zet", constants.DEFAULT_HOURS_PER_ZET))
        tol = int(icp.get_param("ic_urfu.zet_hours_tolerance", 0))
        if hpp <= 0:
            return []

        errors: list[str] = []
        for sem in self.semester_ids.sorted("number"):
            for subj in sem.mandatory_subject_ids | sem.elective_subject_ids:
                expected = _expected_zet_from_hours(subj.hours, hpp)
                if expected == 0:
                    continue
                if abs(subj.credits - expected) > tol:
                    tol_note = f" (допуск ±{tol} ЗЕТ)" if tol else ""
                    errors.append(
                        f"{subj.name} (семестр {sem.number}): указано {subj.credits} ЗЕТ при {subj.hours} ч; "
                        f"по норме {hpp} ч/ЗЕТ ожидается ~{expected}{tol_note}.",
                    )
        return errors

    def _validate_zet_constraints(self):
        """Проверка лимитов ЗЕТ и ауд. нагрузки. Ошибки — ValidationError; предупреждения — список строк.

        Если у выбранного шаблона программы заданы «Мин. ЗЕТ за программу» и/или минимумы по семестрам —
        используются они (не глобальные пороги за семестр). Иначе — настройки из ir.config_parameter.
        """
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        max_weekly = int(icp.get_param("ic_urfu.max_hours_per_week", 36))
        min_zet_global = int(icp.get_param("ic_urfu.min_semester_zet", 25))
        max_zet_global = int(icp.get_param("ic_urfu.max_semester_zet", 35))
        total_norm_global = int(icp.get_param("ic_urfu.total_plan_zet", 240))

        errors: list[str] = []
        warnings: list[str] = []

        errors.extend(self._zet_hour_consistency_errors())

        tmpl = self.program_template_id
        use_template_zet = self._program_template_defines_zet_limits(tmpl)

        for sem in self.semester_ids:
            sn = sem.number
            subjects = sem.mandatory_subject_ids | sem.elective_subject_ids
            total_hours = sum(subjects.mapped("hours"))
            weekly = total_hours / float(constants.WEEKS_PER_SEMESTER)
            if weekly > max_weekly:
                warnings.append(f"Семестр {sn}: ~{weekly:.1f} ч/нед (рекомендуется не более {max_weekly})")
            errors.extend(self._zet_semester_line_errors(sem, tmpl, use_template_zet, min_zet_global, max_zet_global))

        plan_total = self.total_zet

        if use_template_zet:
            if (tmpl.min_total_zet or 0) > 0 and plan_total < tmpl.min_total_zet:
                errors.append(
                    f"Всего по плану {plan_total:g} ЗЕТ; для программы «{tmpl.name}» "
                    f"нужно набрать не менее {tmpl.min_total_zet} ЗЕТ.",
                )
            for st in tmpl.semester_template_ids:
                if (st.min_zet or 0) <= 0:
                    continue
                sn_req = st.semester_number
                if not self.semester_ids.filtered(lambda s, n=sn_req: s.number == n):
                    errors.append(
                        f"В плане нет семестра {sn_req}; по программе для него задано минимум {st.min_zet} ЗЕТ.",
                    )
        elif abs(plan_total - float(total_norm_global)) > constants.PLAN_TOTAL_ZET_TOLERANCE:
            warnings.append(f"Итого по плану: {plan_total:g} ЗЕТ (норма {total_norm_global} ЗЕТ)")

        if errors:
            raise ValidationError("Обнаружены ошибки нагрузки:\n" + "\n".join(f"• {e}" for e in errors))
        return warnings

    def action_apply_template(self):
        """Подставить обязательные дисциплины из шаблона программы в семестры плана."""
        self.ensure_one()
        if not self.program_template_id:
            raise UserError("Выберите шаблон программы перед применением.")

        default_year = "2025 / 2026"
        if self.semester_ids:
            default_year = self.semester_ids[0].academic_year or default_year

        for sem_tmpl in self.program_template_id.semester_template_ids.sorted("semester_number"):
            sn = sem_tmpl.semester_number
            existing = self.semester_ids.filtered(lambda s, n=sn: s.number == n)
            if existing:
                sem = existing[0]
                new_subjects = sem_tmpl.subject_ids - sem.mandatory_subject_ids
                if new_subjects:
                    sem.write({"mandatory_subject_ids": [(4, sid) for sid in new_subjects.ids]})
            else:
                self.env["ic.urfu.semester"].create(
                    {
                        "plan_id": self.id,
                        "number": sem_tmpl.semester_number,
                        "academic_year": default_year,
                        "mandatory_subject_ids": [(6, 0, sem_tmpl.subject_ids.ids)],
                    },
                )

        # Один ответ = одна транзакция без цепочки next (иначе гонка с bus/WebSocket → SerializationFailure).
        self.env.flush_all()
        ctx = dict(self.env.context)
        ctx["form_view_initial_mode"] = "edit"
        tmpl_name = self.program_template_id.name
        return {
            "type": "ir.actions.act_window",
            "name": self.display_name,
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            "context": ctx,
            # Обратная связь без display_notification+next (тост + второе действие ломали WS/commit).
            "effect": {
                "type": "rainbow_man",
                "message": f"Шаблон «{tmpl_name}» применён.",
                "fadeout": "fast",
            },
        }

    def action_suggest_next_modules(self):
        """Добавить в следующий семестр дисциплины-продолжения для модульных спецкурсов."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Предложение модулей доступно только для плана в статусе «Черновик».")

        suggested: list[str] = []
        for sem in self.semester_ids.sorted("number"):
            line = sem.mandatory_subject_ids | sem.elective_subject_ids
            modular_subjects = line.filtered(lambda s: s.is_modular and s.next_module_id)
            if not modular_subjects:
                continue

            next_sem_recs = self.semester_ids.filtered(lambda s, n=sem.number: s.number == n + 1)
            if not next_sem_recs:
                continue

            next_sem = next_sem_recs[0]
            for subj in modular_subjects:
                next_subj = subj.next_module_id
                if not next_subj or not next_subj.exists():
                    continue
                present = next_sem.mandatory_subject_ids | next_sem.elective_subject_ids
                if next_subj in present:
                    continue
                next_sem.write({"elective_subject_ids": [(4, next_subj.id)]})
                suggested.append(f"Семестр {next_sem.number}: «{next_subj.name}»")

        if suggested:
            message = "Добавлены продолжения модулей:\n" + "\n".join(f"• {s}" for s in suggested)
            ntype = "success"
        else:
            message = (
                "Нет цепочек для добавления: задайте у дисциплин «следующую часть модуля» "
                "или части уже стоят в следующем семестре."
            )
            ntype = "info"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": message, "type": ntype, "sticky": bool(suggested)},
        }

    def action_submit(self):
        """Submit plan for teacher review.

        Changes plan state from 'draft' to 'submitted' and sends a notification
        to the teacher via Odoo messaging system.

        Access: Student only

        Returns:
            dict: Notification action if validation fails, otherwise None
        """
        self.ensure_one()

        # Валидация перед отправкой
        if not self.semester_ids:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Ошибка валидации",
                    "message": "Не добавлено ни одного семестра. Добавьте хотя бы один семестр перед отправкой.",
                    "type": "danger",
                    "sticky": False,
                },
            }

        has_disciplines = False
        for semester in self.semester_ids:
            if semester.mandatory_subject_ids or semester.elective_subject_ids:
                has_disciplines = True
                break

        if not has_disciplines:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Ошибка валидации",
                    "message": "Не добавлено ни одной дисциплины в семестры. Добавьте дисциплины перед отправкой.",
                    "type": "danger",
                    "sticky": False,
                },
            }

        warnings = self._validate_zet_constraints()

        self.write({"state": "submitted"})
        # Отправка уведомления преподавателю
        self.message_post(
            body=f"План отправлен на проверку студентом {self.student_id.name}",
            subject="План отправлен на проверку",
            message_type="notification",
        )

        msg = "План отправлен на проверку"
        notif_type = "success"
        if warnings:
            msg += ".\n\nПредупреждение о нагрузке:\n" + "\n".join(warnings)
            notif_type = "warning"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Успешно" if not warnings else "Предупреждение о нагрузке",
                "message": msg,
                "type": notif_type,
                "sticky": bool(warnings),
            },
        }

    def action_approve(self):
        """Approve plan as teacher.

        Changes plan state to 'approved', records the approving teacher,
        and sends a notification to the student.

        Access: Teacher only
        """
        self.write({"state": "approved", "teacher_id": self.env.user.id})
        # Отправка уведомления студенту
        self.message_post(
            body=f"План одобрен преподавателем {self.env.user.name}",
            subject="План одобрен",
            message_type="notification",
            partner_ids=[self.student_id.partner_id.id],
        )

    def action_reject(self):
        """Открыть мастер возврата плана с обязательным комментарием проверяющего."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Возврат плана на доработку",
            "res_model": "ic.urfu.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_plan_id": self.id},
        }

    def action_draft(self):
        """Вернуть в черновик."""
        self.write({"state": "draft", "teacher_comment": False, "rejection_comment": False})

    def unlink(self):
        """Override unlink to restrict deletion based on state.

        Only plans in 'draft' or 'rejected' state can be deleted.
        Plans that are submitted, approved, or have generated documents cannot be deleted.

        Raises:
            UserError: If attempting to delete a plan that is not in draft or rejected state
        """
        for plan in self:
            if plan.state not in ["draft", "rejected"]:
                state_label = dict(plan._fields["state"].selection).get(plan.state, plan.state)
                raise UserError(
                    f"Невозможно удалить план '{plan.name}' в статусе '{state_label}'.\n"
                    f"Удалять можно только черновики и отклонённые планы.",
                )
        return super().unlink()

    def _validate_for_generation(self):
        """Validates plan has all required data for document generation.

        Returns:
            list: List of validation error messages
        """
        self.ensure_one()
        errors = []

        if not self.semester_ids:
            errors.append("- Не добавлено ни одного семестра")

        errors.extend(
            f"- Семестр {semester.number} не содержит дисциплин"
            for semester in self.semester_ids
            if not semester.mandatory_subject_ids and not semester.elective_subject_ids
        )

        if not self.rop_name or not self.rop_name.strip():
            errors.append("- РОП не может быть пустым")

        return errors

    def action_generate_document(self):
        """Генерация документа DOCX."""
        self.ensure_one()

        if self.state != "approved":
            raise UserError("Документ можно генерировать только для одобренных планов!")

        # Валидация данных перед генерацией
        validation_errors = self._validate_for_generation()
        if validation_errors:
            raise UserError("Документ не может быть сгенерирован:\n" + "\n".join(validation_errors))

        try:
            self._validate_zet_constraints()
        except ValidationError as exc:
            raise UserError(str(exc)) from exc

        if create_urfu_plan is None:
            raise UserError("Модуль генерации документов не найден! Убедитесь, что python-docx установлен.")

        # Подготовка данных
        data = self._prepare_document_data()

        # Генерация документа во временный файл
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            create_urfu_plan(data, tmp_path)

            # Чтение файла и сохранение в поле
            with tmp_path.open("rb") as f:
                document_data = f.read()
        except Exception as e:
            raise UserError(f"Ошибка при генерации документа: {e!s}") from e
        finally:
            # Удаление временного файла
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink()

        # Сохранение в запись
        short_safe = (self.student_short_name or "").strip().replace(" ", "_")
        filename = f"Individual_Plan_{short_safe}.docx" if short_safe else f"Individual_Plan_{self.id}.docx"
        self.write(
            {
                "document_file": base64.b64encode(document_data),
                "document_filename": filename,
                "state": "generated",
            },
        )

        # Открываем форму для скачивания
        return {
            "type": "ir.actions.act_window",
            "res_model": "ic.urfu.plan",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def _prepare_document_data(self):
        """Подготовка данных для генератора документов."""
        self.ensure_one()

        # Маппинг форм контроля
        control_map = constants.CONTROL_FORM_MAPPING

        semesters_data = []
        for semester in self.semester_ids.sorted("number"):
            mandatory_subjects = [
                {
                    "name": subj.name,
                    "hours": subj.hours,
                    "credits": subj.credits,
                    "control": control_map.get(subj.control, subj.control),
                }
                for subj in semester.mandatory_subject_ids
            ]

            elective_subjects = [
                {
                    "name": subj.name,
                    "hours": subj.hours,
                    "credits": subj.credits,
                    "control": control_map.get(subj.control, subj.control),
                }
                for subj in semester.elective_subject_ids
            ]

            semesters_data.append(
                {
                    "number": semester.number,
                    "academic_year": semester.academic_year,
                    "mandatory_subjects": mandatory_subjects,
                    "elective_subjects": elective_subjects,
                },
            )

        return {
            "student_name": "",
            "student_short_name": "",
            "rop_name": self.rop_name,
            "year": self.year,
            "institute": self.institute,
            "department": self.department,
            "specialty_code": self.specialty_code,
            "program": self.program,
            "supervisor": self.supervisor or "",
            "research_area": self.research_area or "",
            "thesis_topic": self.thesis_topic or "",
            "deadline": self.deadline,
            "semesters": semesters_data,
        }
