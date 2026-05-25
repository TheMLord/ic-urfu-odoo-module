"""Configuration settings for IC UrFU Module."""

from odoo import fields, models


class IcUrfuConfigSettings(models.TransientModel):
    """Configuration settings for IC UrFU Module.

    This model provides a UI for configuring module defaults and preferences.
    Settings are stored as ir.config_parameter records.
    """

    _name = "ic.urfu.config.settings"
    _inherit = "res.config.settings"
    _description = "IC UrFU Configuration Settings"

    # Document Generation Settings
    # Имена полей без префикса default_: иначе res.config.settings требует default_model (Odoo 17+).
    document_font = fields.Char(
        string="Шрифт документа",
        default="Times New Roman",
        config_parameter="ic_urfu.document_font",
        help="Шрифт для генерируемых DOCX документов",
    )
    document_font_size = fields.Integer(
        string="Размер шрифта",
        default=12,
        config_parameter="ic_urfu.document_font_size",
        help="Размер шрифта в пунктах для документов",
    )

    # Значения по умолчанию для новых дисциплин / планов
    subject_hours = fields.Integer(
        string="Часы по умолчанию",
        default=34,
        config_parameter="ic_urfu.default_hours",
        help="Объем аудиторной работы по умолчанию для новых дисциплин",
    )
    subject_credits = fields.Integer(
        string="ЗЕТ по умолчанию",
        default=3,
        config_parameter="ic_urfu.default_credits",
        help="Количество зачетных единиц по умолчанию для новых дисциплин",
    )
    subject_control_form = fields.Selection(
        [
            ("exam", "Экзамен"),
            ("credit", "Зачет"),
            ("credit_grade", "Зачет с оценкой"),
        ],
        string="Форма аттестации по умолчанию",
        default="credit",
        config_parameter="ic_urfu.default_control_form",
        help="Форма контроля по умолчанию для новых дисциплин",
    )

    plan_institute = fields.Char(
        string="Институт по умолчанию",
        config_parameter="ic_urfu.default_institute",
        help="Название института, автоматически подставляется в новые планы",
    )
    plan_department = fields.Char(
        string="Кафедра/Департамент по умолчанию",
        config_parameter="ic_urfu.default_department",
        help="Название кафедры/департамента, автоматически подставляется в новые планы",
    )

    # Workflow Settings
    notification_enabled = fields.Boolean(
        string="Включить уведомления",
        default=True,
        config_parameter="ic_urfu.notification_enabled",
        help="Отправлять уведомления студентам при изменении статуса плана",
    )

    # Лимиты ЗЕТ и нагрузки (валидация при отправке плана)
    min_semester_zet = fields.Integer(
        string="Мин. ЗЕТ за семестр",
        default=25,
        config_parameter="ic_urfu.min_semester_zet",
        help="Минимальная сумма ЗЕТ по дисциплинам семестра",
    )
    max_semester_zet = fields.Integer(
        string="Макс. ЗЕТ за семестр",
        default=35,
        config_parameter="ic_urfu.max_semester_zet",
        help="Максимальная сумма ЗЕТ по дисциплинам семестра",
    )
    total_plan_zet = fields.Integer(
        string="Норма ЗЕТ за весь план",
        default=240,
        config_parameter="ic_urfu.total_plan_zet",
        help="Целевая сумма ЗЕТ по программе (отклонение допускается с предупреждением)",
    )
    max_hours_per_week = fields.Integer(
        string="Макс. ауд. часов в неделю",
        default=36,
        config_parameter="ic_urfu.max_hours_per_week",
        help="Рекомендуемый потолок средней недельной аудиторной нагрузки в семестре",
    )

    hours_per_zet = fields.Integer(
        string="Ауд. часов на 1 ЗЕТ",
        default=12,
        config_parameter="ic_urfu.hours_per_zet",
        help="Ожидаемое ЗЭТ для дисциплины ≈ округление (аудиторные часы / это значение). "
        "Для справочника-демо подходит 12; для проверки по методике с 36 ч/ЗЭТ укажите 36.",
    )
    zet_hours_tolerance = fields.Integer(
        string="Допуск ЗЕТ (±)",
        default=0,
        config_parameter="ic_urfu.zet_hours_tolerance",
        help="Допустимое отклонение указанного ЗЭТ от расчёта по часам (в зачётных единицах).",
    )
    enforce_hours_zet = fields.Boolean(
        string="Проверять соответствие часов и ЗЭТ при отправке и генерации документа",
        default=True,
        config_parameter="ic_urfu.enforce_hours_zet",
    )
