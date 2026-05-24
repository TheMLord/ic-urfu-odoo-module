"""Subject (дисциплина) и справочник слотов семестров.

- ic.urfu.subject: каталог дисциплин (обязательная/по выбору, часы, ЗЕТ, форма аттестации,
  модульные цепочки, допустимые слоты семестров).
- ic.urfu.semester.slot: фиксированный справочник номеров 1..8 (seedится из data/semester_slots.xml).
"""

from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .. import constants
from ._helpers import _expected_zet_from_hours


class Subject(models.Model):
    """Course/Discipline model.

    Represents an academic course with its workload parameters.
    Subjects can be mandatory or elective, and are assigned to semesters
    within an individual education plan.

    Fields:
        name: Course name (unique)
        hours: Auditorium work hours
        credits: Credit units (ЗЕТ)
        control: Assessment form (exam, credit, graded credit)
        subject_type: Type (mandatory or elective)
    """

    _name = "ic.urfu.subject"
    _description = "Subject/Course"
    _order = "name"

    name = fields.Char("Наименование дисциплины", required=True)
    hours = fields.Integer(
        "Объем аудит. работы, час",
        default=lambda self: int(
            self.env["ir.config_parameter"].sudo().get_param("ic_urfu.default_hours", constants.DEFAULT_HOURS)
        ),
    )
    credits = fields.Integer(
        "Объем (зет)",
        default=lambda self: int(
            self.env["ir.config_parameter"].sudo().get_param("ic_urfu.default_credits", constants.DEFAULT_CREDITS)
        ),
    )
    control = fields.Selection(
        [
            ("exam", "Экзамен"),
            ("credit", "Зачет"),
            ("credit_grade", "Зачет с оценкой"),
        ],
        string="Форма аттестации",
        default=lambda self: (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ic_urfu.default_control_form", constants.DEFAULT_CONTROL_FORM)
        ),
    )
    subject_type = fields.Selection(
        [
            ("mandatory", "Обязательная"),
            ("elective", "По выбору"),
        ],
        string="Тип дисциплины",
        default="mandatory",
    )

    is_modular = fields.Boolean(
        string="Модульный спецкурс",
        default=False,
        help="Цепочка частей курса: следующая часть подставляется в следующий семестр командой на плане.",
    )
    next_module_id = fields.Many2one(
        "ic.urfu.subject",
        string="Следующая часть модуля",
        ondelete="set null",
        domain="[('subject_type', '=', 'elective'), ('id', '!=', id)]",
    )
    zet_from_hours = fields.Integer(
        string="ЗЕТ по норме часов",
        compute="_compute_zet_from_hours",
        help="Округление ауд. часов к норме из настроек (часов на 1 ЗЭТ).",
    )
    allowed_semester_ids = fields.Many2many(
        "ic.urfu.semester.slot",
        "subject_allowed_semester_rel",
        "subject_id",
        "slot_id",
        string="Доступно в семестрах",
        help="В каких семестрах эту дисциплину можно ставить в план. "
        "Если задан шаблон программы, для обязательных дисциплин приоритет имеет шаблон.",
    )

    @api.depends("hours")
    def _compute_zet_from_hours(self):
        icp = self.env["ir.config_parameter"].sudo()
        hpp = int(icp.get_param("ic_urfu.hours_per_zet", constants.DEFAULT_HOURS_PER_ZET))
        for rec in self:
            rec.zet_from_hours = _expected_zet_from_hours(rec.hours, hpp)

    @api.constrains("hours", "credits")
    def _check_positive_values(self):
        """Validate that hours and credits are positive.

        Ensures that both auditorium hours and credit units are greater than zero.

        Raises:
            ValidationError: If hours or credits are less than or equal to zero.
        """
        for record in self:
            if record.hours <= 0:
                raise ValidationError("Объем аудиторной работы должен быть больше 0!")
            if record.credits <= 0:
                raise ValidationError("Объем (ЗЕТ) должен быть больше 0!")

    _sql_constraints: ClassVar[list[tuple[str, str, str]]] = [
        ("name_unique", "unique(name)", "Дисциплина с таким названием уже существует!"),
    ]

    @api.constrains("is_modular", "next_module_id", "subject_type")
    def _check_modular_chain(self):
        for rec in self:
            if rec.next_module_id:
                if not rec.is_modular:
                    raise ValidationError(
                        "Укажите флаг «Модульный спецкурс», если задана следующая часть модуля.",
                    )
                if rec.next_module_id.id == rec.id:
                    raise ValidationError("Дисциплина не может ссылаться на себя как на следующую часть модуля.")
                if rec.next_module_id.subject_type != "elective":
                    raise ValidationError("Следующая часть модуля должна быть дисциплиной «По выбору».")
            if rec.is_modular and rec.subject_type != "elective":
                raise ValidationError("Модульный спецкурс может быть только дисциплиной по выбору.")


class SemesterSlot(models.Model):
    """Справочник «слотов» номера семестра (1..8).

    Используется для свойства дисциплины «в каких семестрах её можно ставить в план»
    (ic.urfu.subject.allowed_semester_ids). Записи seedятся через data/semester_slots.xml.
    """

    _name = "ic.urfu.semester.slot"
    _description = "Семестр (справочник номеров)"
    _order = "number"

    number = fields.Integer("Номер семестра", required=True)
    name = fields.Char("Название", compute="_compute_name", store=True)

    _sql_constraints: ClassVar[list[tuple[str, str, str]]] = [
        ("number_uniq", "unique(number)", "Слот семестра с таким номером уже существует!"),
    ]

    @api.depends("number")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.number} семестр" if rec.number else ""

    @api.constrains("number")
    def _check_number_range(self):
        for rec in self:
            if rec.number < 1 or rec.number > 8:
                raise ValidationError("Номер семестра должен быть от 1 до 8.")
