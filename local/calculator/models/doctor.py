from odoo import models, fields, api
import math


class doctor(models.Model):
    _name = 'hc.doctor'
    name = fields.Char(string='姓名')
    p_num = fields.Integer(string='患者数量')
    pci_num = fields.Integer(string='月PCI上转')
    ecg_num = fields.Integer(string='月心电图次数')
    follow_up_num = fields.Integer(string='月随访次数')

    calculator_id = fields.Many2many('hc.calculator', 'hc_calculator_doctor_rel', 'doctor_id', 'calculator_id',
                                     string='关联计算器')

    pci_referral_incentive_amount = fields.Float(
        '一次PCI上转激励金额',
        related='calculator_id.pci_referral_incentive_amount',
        readonly=True)

    ecg_incentive_amount = fields.Float(
        '一次心电图激励金额',
        related='calculator_id.ecg_incentive_amount',
        readonly=True)

    follow_up_incentive_amount = fields.Float(
        '一次随访激励金额',
        related='calculator_id.follow_up_incentive_amount',
        readonly=True)

    pci_amount_per_month = fields.Float(
        '月PCI激励',
        compute='_compute_pci_amount_per_month',
        readonly=True)

    @api.depends("pci_referral_incentive_amount", "pci_num")
    def _compute_pci_amount_per_month(self):
        for rec in self:
            rec.pci_amount_per_month = rec.pci_referral_incentive_amount * rec.pci_num

    ecg_amount_per_month = fields.Float(
        '月心电图激励',
        compute='_compute_ecg_amount_per_month',
        readonly=True)

    @api.depends("ecg_incentive_amount", "ecg_num")
    def _compute_ecg_amount_per_month(self):
        for rec in self:
            rec.ecg_amount_per_month = rec.ecg_incentive_amount * rec.ecg_num

    follow_up_amount_per_month = fields.Float(
        '月随访激励',
        compute='_compute_follow_up_amount_per_month',
        readonly=True)

    @api.depends("ecg_incentive_amount", "ecg_num")
    def _compute_follow_up_amount_per_month(self):
        for rec in self:
            rec.follow_up_amount_per_month = rec.follow_up_incentive_amount * rec.follow_up_num

    total_incentive_amount = fields.Float("月激励总计", compute='_compute_total_incentive_amount', readonly=True)

    def _compute_total_incentive_amount(self):
        for rec in self:
            rec.total_incentive_amount = rec.pci_amount_per_month + rec.ecg_amount_per_month + rec.follow_up_amount_per_month


