"""Семестр в составе индивидуального плана."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Semester(models.Model):
    """Study Semester model.

    Represents a semester within an individual education plan.
    Contains mandatory and elective subjects for that semester.

    Fields:
        name: Computed name (number + academic year)
        number: Semester number (1-8)
        academic_year: Academic year string (e.g., "2025 / 2026")
        plan_id: Reference to parent individual plan
        mandatory_subject_ids: Mandatory subjects for this semester
        elective_subject_ids: Elective subjects for this semester
    """

    _name = "ic.urfu.semester"
    _description = "Study Semester"
    _order = "number"

    name = fields.Char("Название", compute="_compute_name", store=False)
    number = fields.Integer("Номер семестра", required=True)
    academic_year = fields.Char("Учебный год", required=True, default="2025 / 2026")
    plan_id = fields.Many2one("ic.urfu.plan", string="Индивидуальный план", ondelete="cascade")

    # Дисциплины
    mandatory_subject_ids = fields.Many2many(
        "ic.urfu.subject",
        "semester_mandatory_subject_rel",
        "semester_id",
        "subject_id",
        string="Обязательные дисциплины",
        domain=[("subject_type", "=", "mandatory")],
    )
    elective_subject_ids = fields.Many2many(
        "ic.urfu.subject",
        "semester_elective_subject_rel",
        "semester_id",
        "subject_id",
        string="Дисциплины по выбору",
        domain=[("subject_type", "=", "elective")],
    )

    zet_total = fields.Float(
        string="Итого ЗЕТ",
        compute="_compute_zet_total",
        store=True,
        help="Сумма ЗЕТ (поле «Объем (зет)» дисциплин) по обязательным и выборным дисциплинам семестра",
    )

    available_mandatory_subject_ids = fields.Many2many(
        "ic.urfu.subject",
        "semester_available_mandatory_rel",
        "semester_id",
        "subject_id",
        compute="_compute_available_subjects",
        compute_sudo=True,
        string="Доступные обязательные",
        help="Пул обязательных дисциплин для этого семестра. "
        "Если у плана выбран шаблон программы — берётся из шаблона, иначе из allowed_semester_ids дисциплин.",
    )
    available_elective_subject_ids = fields.Many2many(
        "ic.urfu.subject",
        "semester_available_elective_rel",
        "semester_id",
        "subject_id",
        compute="_compute_available_subjects",
        compute_sudo=True,
        string="Доступные по выбору",
        help="Пул выборных дисциплин для этого семестра по allowed_semester_ids.",
    )

    @api.depends("mandatory_subject_ids.credits", "elective_subject_ids.credits")
    def _compute_zet_total(self):
        for sem in self:
            zet = sum(sem.mandatory_subject_ids.mapped("credits"))
            zet += sum(sem.elective_subject_ids.mapped("credits"))
            sem.zet_total = float(zet)

    @api.depends(
        "number",
        "plan_id.program_template_id",
        "plan_id.program_template_id.semester_template_ids.semester_number",
        "plan_id.program_template_id.semester_template_ids.subject_ids",
    )
    def _compute_available_subjects(self):
        subject_env = self.env["ic.urfu.subject"].sudo()
        for sem in self:
            sn = sem.number
            tmpl = sem.plan_id.program_template_id
            sem_tmpl = (
                tmpl.semester_template_ids.filtered(lambda t, n=sn: t.semester_number == n)[:1] if tmpl else False
            )
            if sem_tmpl and sem_tmpl.subject_ids:
                mandatory_pool = sem_tmpl.subject_ids
            else:
                mandatory_pool = subject_env.search(
                    [("subject_type", "=", "mandatory"), ("allowed_semester_ids.number", "=", sn)],
                )
            sem.available_mandatory_subject_ids = mandatory_pool
            sem.available_elective_subject_ids = subject_env.search(
                [("subject_type", "=", "elective"), ("allowed_semester_ids.number", "=", sn)],
            )

    @api.constrains("number")
    def _check_semester_number(self):
        """Validate semester number is within valid range.

        Master's programs at UrFU typically span 1-8 semesters.

        Raises:
            ValidationError: If semester number is not between 1 and 8.
        """
        for record in self:
            if record.number <= 0 or record.number > 8:
                raise ValidationError("Номер семестра должен быть от 1 до 8!")

    @api.constrains("plan_id", "number")
    def _check_unique_semester_number(self):
        """Validate semester number is unique within the plan.

        Each individual plan can have only one semester with a given number.

        Raises:
            ValidationError: If another semester with the same number exists in this plan.
        """
        for record in self:
            if record.plan_id:
                duplicate = self.search(
                    [("plan_id", "=", record.plan_id.id), ("number", "=", record.number), ("id", "!=", record.id)],
                )
                if duplicate:
                    raise ValidationError(f"Семестр {record.number} уже существует в этом плане!")

    @api.depends("number", "academic_year")
    def _compute_name(self):
        """Compute semester display name.

        Generates a human-readable name combining semester number and academic year.
        Example: "1 семестр (2025 / 2026)"
        """
        for record in self:
            record.name = f"{record.number} семестр ({record.academic_year})"
