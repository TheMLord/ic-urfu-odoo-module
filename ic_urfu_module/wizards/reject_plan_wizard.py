# Copyright <2026> IC UrFU
# License LGPL-3

from markupsafe import escape
from odoo import fields, models
from odoo.exceptions import UserError


class RejectPlanWizard(models.TransientModel):
    _name = "ic.urfu.reject.wizard"
    _description = "Wizard возврата плана на доработку"

    plan_id = fields.Many2one("ic.urfu.plan", string="План", required=True, readonly=True)
    comment = fields.Text(
        string="Причина возврата",
        required=True,
        help="Обязательно укажите, что именно нужно исправить студенту",
    )

    def action_confirm_reject(self):
        self.ensure_one()
        if not (self.comment and self.comment.strip()):
            raise UserError("Укажите причину возврата плана.")
        plan = self.plan_id
        plan.write(
            {
                "state": "rejected",
                "teacher_id": self.env.user.id,
                "rejection_comment": self.comment.strip(),
                "teacher_comment": False,
            }
        )
        safe = escape(self.comment.strip())
        plan.message_post(
            body=f"<b>План возвращён на доработку.</b><br/>Комментарий проверяющего: {safe}",
            subtype_xmlid="mail.mt_comment",
            message_type="notification",
            partner_ids=[plan.student_id.partner_id.id],
        )
        return {"type": "ir.actions.act_window_close"}
