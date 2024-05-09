
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    start_time = fields.Datetime(string="开始时间")
    end_time = fields.Datetime(string="结束时间")

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param('rank.start_time', self.start_time)
        self.env["ir.config_parameter"].sudo().set_param('rank.end_time', self.end_time)
        return res

    def get_values(self):
        res = super().get_values()

        start_time = self.env["ir.config_parameter"].sudo().get_param('rank.start_time')
        end_time = self.env["ir.config_parameter"].sudo().get_param('rank.end_time')

        res.update(
            start_time=start_time,
            end_time=end_time,
        )
        return res
