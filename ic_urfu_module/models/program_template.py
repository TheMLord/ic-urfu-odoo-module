"""Шаблон образовательной программы и шаблон семестра внутри программы."""

from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProgramTemplate(models.Model):
    """Шаблон образовательной программы (направление + набор обязательных дисциплин по семестрам)."""

    _name = "ic.urfu.program.template"
    _description = "Шаблон образовательной программы"
    _order = "code, name"

    name = fields.Char("Название программы", required=True)
    code = fields.Char("Код направления")
    min_total_zet = fields.Integer(
        string="Мин. ЗЕТ за программу (всего)",
        default=0,
        help="Сумма ЗЕТ по всем семестрам плана не должна быть меньше этого значения. "
        "0 — не задавать минимум по программе (только по семестрам или глобальные лимиты).",
    )
    semester_template_ids = fields.One2many(
        "ic.urfu.semester.template",
        "program_id",
        string="Семестры шаблона",
    )


class SemesterTemplate(models.Model):
    """Строка шаблона: номер семестра и обязательные дисциплины."""

    _name = "ic.urfu.semester.template"
    _description = "Шаблон семестра для программы"
    _order = "semester_number"

    program_id = fields.Many2one(
        "ic.urfu.program.template",
        string="Программа",
        required=True,
        ondelete="cascade",
    )
    semester_number = fields.Integer("Номер семестра", required=True)
    min_zet = fields.Integer(
        string="Мин. ЗЕТ в семестре",
        default=0,
        help="Минимум суммы ЗЕТ по дисциплинам этого семестра в индивидуальном плане. "
        "0 — не требовать отдельный минимум для этого семестра.",
    )
    subject_ids = fields.Many2many(
        "ic.urfu.subject",
        "semester_template_subject_rel",
        "semester_template_id",
        "subject_id",
        string="Обязательные дисциплины шаблона",
        domain=[("subject_type", "=", "mandatory")],
    )

    @api.constrains("semester_number")
    def _check_semester_number_template(self):
        for rec in self:
            if rec.semester_number < 1 or rec.semester_number > 8:
                raise ValidationError("Номер семестра в шаблоне должен быть от 1 до 8!")

    _sql_constraints: ClassVar[list[tuple[str, str, str]]] = [
        (
            "program_template_semester_uniq",
            "unique(program_id, semester_number)",
            "В шаблоне программы уже задан этот номер семестра!",
        ),
    ]
