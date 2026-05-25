# Copyright <2026> Michael <->
# License MIT
{
    "name": "IC UrFU Module",
    "summary": "Individual education plan generator for UrFU",
    "version": "17.0.1.0.7",
    "development_status": "Beta",
    "category": "Education",
    "website": "-",
    "author": "<->",
    "maintainers": ["TheMLord"],
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "depends": ["base", "web", "mail"],
    "external_dependencies": {
        # PyPI distribution name (import is still `docx`)
        "python": ["python-docx"],
    },
    "data": [
        "security/ic_urfu_security.xml",
        "security/ir.model.access.csv",
        "data/demo_users.xml",
        "views/ic_urfu_views.xml",
        "views/ic_urfu_config_views.xml",
        "views/program_template_views.xml",
        "views/reject_plan_wizard_views.xml",
    ],
    "demo": [
        "demo/demo_subjects.xml",
        "data/program_template_data.xml",
        "demo/demo_plans.xml",
    ],
}
