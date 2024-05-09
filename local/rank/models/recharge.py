from odoo import models, fields, api
import math
import pandas as pd


class Recharge(models.Model):
    _name = 'rank.recharge'
    transaction_time = fields.Datetime(string='交易时间')
    phone_num = fields.Char(string='手机号')
    transaction_serial_code = fields.Char(string='交易流水号', unique=True)
    transaction_order_code = fields.Char(string='交易单号')
    card_num = fields.Char(string='会员卡号')
    transaction_amount = fields.Float(string='交易金额')
    action_type = fields.Char(string='操作类型')
