"""Constants for IC UrFU Module.

This module contains all hardcoded values used throughout the application.
Centralizing constants makes it easier to maintain and modify default values.
"""

# Document Generation
DEFAULT_FONT_NAME = "Times New Roman"
DEFAULT_FONT_SIZE = 12
DEFAULT_DOCUMENT_FILENAME_PREFIX = "Individual_Plan"

# Document Header Text
DOCUMENT_HEADER_LINE1 = "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ"
DOCUMENT_HEADER_LINE2 = "Федеральное государственное автономное образовательное учреждение высшего образования"
DOCUMENT_HEADER_LINE3 = "«Уральский федеральный университет имени первого Президента России Б.Н.Ельцина»"
DOCUMENT_TITLE = "ИНДИВИДУАЛЬНЫЙ УЧЕБНЫЙ ПЛАН МАГИСТРАНТА"

# Section Labels
SECTION_GENERAL_INFO = "Общие сведения"
SECTION_EDUCATION_PART = "Образовательная часть программы подготовки"
SECTION_MANDATORY = "Обязательная часть в соответствии с учебным планом"
SECTION_ELECTIVE = "Дисциплины и курсы по выбору и факультативы"
SECTION_CONCLUSION = "Заключение кафедры:"

# Field Labels
LABEL_INSTITUTE = "Институт"
LABEL_DEPARTMENT = "Кафедра/Департамент"
LABEL_SPECIALTY = "Направление подготовки"
LABEL_PROGRAM = "Образовательная программа"
LABEL_SUPERVISOR = "Научный руководитель"
LABEL_RESEARCH_AREA = "Направление научно-исследовательской деятельности"
LABEL_THESIS = "Тема выпускной квалификационной работы"
LABEL_DEADLINE = "Срок предоставления ВКР к защите"

# Table Headers
TABLE_HEADERS_SUBJECTS = [
    "№ п/п",
    "Наименование дисциплин, практик",
    "Объем аудит. работы, час",
    "Объем (зет)",
    "Форма аттестации",
    "Оценка",
]

# Control Forms Mapping
CONTROL_FORM_MAPPING = {
    "exam": "Экзамен",
    "credit": "Зачет",
    "credit_grade": "Зачет с оценкой",
}

# Validation Limits
MIN_SEMESTER_NUMBER = 1
MAX_SEMESTER_NUMBER = 8
MIN_HOURS = 1
MAX_HOURS = 200
MIN_CREDITS = 1
MAX_CREDITS = 10

# Зачётные единицы (ЗЕТ): соответствие аудиторных часов и ЗЕТ задаётся в настройках (ic_urfu.hours_per_zet).
DEFAULT_HOURS_PER_ZET = 12

# Default Values
DEFAULT_HOURS = 34
DEFAULT_CREDITS = 3
DEFAULT_CONTROL_FORM = "credit"
DEFAULT_ACADEMIC_YEAR = "2025 / 2026"
DEFAULT_YEAR = "2025"
DEFAULT_DEADLINE = "Май 2027"

# Document Formatting
SEPARATOR_LENGTH_SHORT = 40
SEPARATOR_LENGTH_LONG = 80
