import os

from odoo import models, fields, api
import math, requests
import pyecharts.options as opts
from pyecharts.charts import Line

class calculator(models.Model):
    _name = 'hc.calculator'

    doctor_id = fields.Many2many('hc.doctor', 'hc_calculator_doctor_rel', 'calculator_id', 'doctor_id',
                                 string='关联医生')

    county_total_population = fields.Integer(string='县域总人口数', default=1000000)
    county_previous_year_pci_quantity = fields.Integer(string='县域上一年度PCI数量', default=280)

    town_population = fields.Integer(string='所辖乡镇人口数', default=85630)
    town_estimated_high_risk_population = fields.Integer(string='所辖乡镇预计高危人群数', compute='_compute_high_risk_population', readonly=True)
    town_theoretical_annual_pci_estimation = fields.Integer(string='所辖乡镇理论年度PCI量预估', compute='_compute_annual_pci_estimation', readonly=True)
    town_previous_year_pci_quantity_estimation = fields.Integer(string='所辖乡镇上一年度PCI数量(推算)', compute='_compute_previous_year_pci', readonly=True)

    planned_pci_ratio_to_theoretical_quantity = fields.Float(string='计划可获PCI占比(对比理论数量)', digits=(16, 2), default=0.7)
    planned_high_risk_population_management_ratio = fields.Float(string='计划高危人群管理占比', compute='_compute_high_risk_ratio', readonly=True)
    planned_high_risk_population_management_quantity = fields.Integer(string='计划高危人群管理数量', compute='_compute_high_risk_quantity', readonly=True)
    predicted_pci_quantity_obtainable = fields.Integer(string='所辖乡镇可获得PCI数量(预测)', compute='_compute_pci_quantity', readonly=True)

    average_family_doctor_managed_high_risk_population = fields.Integer(string='平均家医管理高危人数', default=50)
    average_family_doctor_incentive_amount_per_month = fields.Integer(string='平均家医激励金额/月', default=1000)
    family_doctor_incentive_distribution_ratio = fields.Float(string='家医激励分配比例', default=0.8)
    town_incentive_distribution_ratio = fields.Float(string='乡镇激励分配比例', default=0.1)
    hospital_incentive_distribution_ratio = fields.Float(string='医院激励分配比例', compute="_compute_hospital_incentive_distribution_ratio", readonly=True)

    @api.depends("family_doctor_incentive_distribution_ratio", "town_incentive_distribution_ratio")
    def _compute_hospital_incentive_distribution_ratio(self):
        for rec in self:
            rec.hospital_incentive_distribution_ratio = 1 - rec.family_doctor_incentive_distribution_ratio - rec.town_incentive_distribution_ratio

    required_family_doctor_count = fields.Integer(string='所需家医人数', compute='_compute_family_doctor_count', readonly=True)
    family_doctor_incentive_investment = fields.Float(string='家医激励投入', compute='_compute_family_doctor_incentive_investment', digits=(16, 0), readonly=True)
    town_incentive_investment = fields.Float(string='乡镇激励投入', compute='_compute_town_incentive_investment', digits=(16, 0), readonly=True)
    hospital_incentive_investment = fields.Float(string='医院激励投入', compute='_compute_hospital_incentive_investment', digits=(16, 0), readonly=True)
    total_incentive_investment = fields.Float(string='激励投入总计', compute='_compute_total_incentive_investment', digits=(16, 0), readonly=True)

    pci_medical_insurance_payment_limit = fields.Float(string='PCI医保支付额度', default=40000, digits=(16, 0))
    pci_average_accounting_cost = fields.Float(string='PCI平均核算成本', default=15000, digits=(16, 0))
    annual_increment_pci_revenue = fields.Float(string='年度增量PCI收益', compute='_compute_annual_increment_pci_revenue', digits=(16, 0), readonly=True)
    annual_management_incremental_revenue_estimate = fields.Float(string='年度管理实施综合增量收益(预估)', digits=(16, 0), compute='_compute_annual_management_incremental_revenue', readonly=True)

    avg_patient_per_family_doctor_per_month = fields.Integer(string='每位家医月管理患者平均人数', default=50)
    max_follow_up_per_patient_per_month = fields.Integer(string='每位家医月随访次数/患者(最多)', default=4)
    max_follow_up_per_month = fields.Integer(string='每位家医月随访次数', compute='_compute_max_follow_up_per_month', readonly=True)

    @api.depends("avg_patient_per_family_doctor_per_month", "max_follow_up_per_patient_per_month")
    def _compute_max_follow_up_per_month(self):
        for rec in self:
            rec.max_follow_up_per_month = rec.avg_patient_per_family_doctor_per_month * rec.max_follow_up_per_patient_per_month

    max_ecg_per_patient_per_month = fields.Integer(string='每位家医月心电图次数/患者(最多)', default=1)
    max_ecg_per_month = fields.Integer(string='每位家医月心电图次数', compute='_compute_max_ecg_per_month', readonly=True)

    @api.depends("avg_patient_per_family_doctor_per_month", "max_ecg_per_patient_per_month")
    def _compute_max_ecg_per_month(self):
        for rec in self:
            rec.max_ecg_per_month = rec.avg_patient_per_family_doctor_per_month * rec.max_ecg_per_patient_per_month

    avg_pci_referral_per_family_doctor_per_month = fields.Float(string='每位家医月度平均PCI上转数量', compute='_compute_avg_pci_referral_per_family_doctor_per_month')
    avg_pci_referral_per_family_doctor_per_quarter = fields.Float(string='每位家医季度平均PCI上转数量', default=1)

    @api.depends("avg_pci_referral_per_family_doctor_per_quarter")
    def _compute_avg_pci_referral_per_family_doctor_per_month(self):
        for rec in self:
            rec.avg_pci_referral_per_family_doctor_per_month = rec.avg_pci_referral_per_family_doctor_per_quarter / 3

    avg_monthly_incentive_budget_per_family_doctor = fields.Float(string='家医人均月激励金额预算', default=1000)
    pci_incentive_value_ratio = fields.Float(string='PCI激励价值占比', digits=(16, 2), default=0.2)
    ecg_incentive_value_ratio = fields.Float(string='心电图激励价值占比', digits=(16, 2), default=0.5)

    follow_up_incentive_value_ratio = fields.Float(string='随访激励价值占比', compute='_compute_follow_up_incentive_value_ratio', digits=(16, 2), readonly=True)

    @api.depends("pci_incentive_value_ratio", "ecg_incentive_value_ratio")
    def _compute_follow_up_incentive_value_ratio(self):
        for rec in self:
            rec.follow_up_incentive_value_ratio = 1 - rec.pci_incentive_value_ratio - rec.ecg_incentive_value_ratio

    follow_up_weight = fields.Float(string='随访权重', default=1)
    ecg_weight = fields.Float(string='心电权重', compute='_compute_ecg_weight', readonly=True)

    @api.depends("follow_up_weight", "max_follow_up_per_month", "follow_up_incentive_value_ratio", "ecg_incentive_value_ratio", "max_ecg_per_month")
    def _compute_ecg_weight(self):
        for rec in self:
            if rec.follow_up_incentive_value_ratio and rec.ecg_incentive_value_ratio and rec.max_ecg_per_month:
                rec.ecg_weight = rec.follow_up_weight * rec.max_follow_up_per_month / rec.follow_up_incentive_value_ratio * rec.ecg_incentive_value_ratio / rec.max_ecg_per_month
            else:
                rec.ecg_weight = 0

    pci_weight = fields.Float(string='PCI权重', compute='_compute_pci_weight', readonly=True)

    @api.depends("follow_up_weight", "max_follow_up_per_month", "follow_up_incentive_value_ratio", "pci_incentive_value_ratio", "avg_pci_referral_per_family_doctor_per_month")
    def _compute_pci_weight(self):
        for rec in self:
            if rec.follow_up_incentive_value_ratio and rec.pci_incentive_value_ratio and rec.avg_pci_referral_per_family_doctor_per_month:
                rec.pci_weight = rec.follow_up_weight * rec.max_follow_up_per_month / rec.follow_up_incentive_value_ratio * rec.pci_incentive_value_ratio / rec.avg_pci_referral_per_family_doctor_per_month
            else:
                rec.pci_weight = 0

    pci_score = fields.Float(string='PCI积分', digits=(16, 2), compute='_compute_pci_score', readonly=True)

    @api.depends("avg_pci_referral_per_family_doctor_per_month", "pci_weight")
    def _compute_pci_score(self):
        for rec in self:
            rec.pci_score = rec.avg_pci_referral_per_family_doctor_per_month * rec.pci_weight

    ecg_score = fields.Float(string='心电积分', digits=(16, 2), compute='_compute_ecg_score', readonly=True)

    @api.depends("max_ecg_per_month", "ecg_weight")
    def _compute_ecg_score(self):
        for rec in self:
            rec.ecg_score = rec.max_ecg_per_month * rec.ecg_weight

    follow_up_score = fields.Float(string='随访积分', digits=(16, 2), compute='_compute_follow_up_score', readonly=True)

    @api.depends("max_follow_up_per_month", "follow_up_weight")
    def _compute_follow_up_score(self):
        for rec in self:
            rec.follow_up_score = rec.max_follow_up_per_month * rec.follow_up_weight

    weight_score = fields.Float(string='权重值', digits=(16, 2), compute='_compute_weight_score', readonly=True)

    @api.depends("avg_monthly_incentive_budget_per_family_doctor", "pci_score", "ecg_score", "follow_up_score")
    def _compute_weight_score(self):
        for rec in self:
            if rec.pci_score + rec.ecg_score + rec.follow_up_score:
                rec.weight_score = rec.avg_monthly_incentive_budget_per_family_doctor / (rec.pci_score + rec.ecg_score + rec.follow_up_score)
            else:
                rec.weight_score = 0

    pci_incentive_amount_per_family_doctor_per_month = fields.Float(string='每位家医月PCI激励金额上限', digits=(16, 1), compute="_compute_pci_incentive_amount_per_family_doctor_per_month", readonly=True)

    @api.depends("pci_score", "weight_score")
    def _compute_pci_incentive_amount_per_family_doctor_per_month(self):
        for rec in self:
            rec.pci_incentive_amount_per_family_doctor_per_month = rec.pci_score * rec.weight_score

    ecg_incentive_amount_per_family_doctor_per_month = fields.Float(string='每位家医月心电激励金额上限', digits=(16, 1), compute="_compute_ecg_incentive_amount_per_family_doctor_per_month", readonly=True)

    @api.depends("pci_score", "weight_score")
    def _compute_ecg_incentive_amount_per_family_doctor_per_month(self):
        for rec in self:
            rec.ecg_incentive_amount_per_family_doctor_per_month = rec.ecg_score * rec.weight_score

    follow_up_incentive_amount_per_family_doctor_per_month = fields.Float(string='每位家医月随访激励金额上限', digits=(16, 1), compute="_compute_follow_up_incentive_amount_per_family_doctor_per_month",
                                                                          readonly=True)

    @api.depends("follow_up_score", "weight_score")
    def _compute_follow_up_incentive_amount_per_family_doctor_per_month(self):
        for rec in self:
            rec.follow_up_incentive_amount_per_family_doctor_per_month = rec.follow_up_score * rec.weight_score

    total_incentive_amount_per_family_doctor_per_month = fields.Float(string='每位家医激励金额总计上限', digits=(16, 1), compute="_compute_total_incentive_amount_per_family_doctor_per_month",
                                                                      readonly=True)

    @api.depends("follow_up_incentive_amount_per_family_doctor_per_month", "ecg_incentive_amount_per_family_doctor_per_month", "pci_incentive_amount_per_family_doctor_per_month")
    def _compute_total_incentive_amount_per_family_doctor_per_month(self):
        for rec in self:
            rec.total_incentive_amount_per_family_doctor_per_month = rec.follow_up_incentive_amount_per_family_doctor_per_month + rec.ecg_incentive_amount_per_family_doctor_per_month + rec.pci_incentive_amount_per_family_doctor_per_month

    pci_referral_incentive_amount = fields.Float(string='一次PCI上转激励金额', compute='_compute_pci_referral_incentive_amount', readonly=True)

    @api.depends("pci_weight", "weight_score")
    def _compute_pci_referral_incentive_amount(self):
        for rec in self:
            rec.pci_referral_incentive_amount = rec.pci_weight * rec.weight_score

    ecg_incentive_amount = fields.Float(string='一次心电图激励金额', compute='_compute_ecg_incentive_amount', readonly=True)

    @api.depends("ecg_weight", "weight_score")
    def _compute_ecg_incentive_amount(self):
        for rec in self:
            rec.ecg_incentive_amount = rec.ecg_weight * rec.weight_score

    follow_up_incentive_amount = fields.Float(string='一次随访激励金额', compute='_compute_follow_up_incentive_amount', readonly=True)

    @api.depends("follow_up_weight", "weight_score")
    def _compute_follow_up_incentive_amount(self):
        for rec in self:
            rec.follow_up_incentive_amount = rec.follow_up_weight * rec.weight_score

    monthly_ecg_incentive_amount_limit = fields.Float(string='月度心电图激励金额上限', digits=(16, 0))
    monthly_follow_up_incentive_amount_limit = fields.Float(string='月度随访激励金额上限', digits=(16, 0))

    # 参数设定

    @api.depends("town_population")
    def _compute_high_risk_population(self):
        for rec in self:
            rec.town_estimated_high_risk_population = math.ceil(rec.town_population * 0.1)

    @api.depends("town_estimated_high_risk_population")
    def _compute_annual_pci_estimation(self):
        for rec in self:
            rec.town_theoretical_annual_pci_estimation = math.ceil(rec.town_estimated_high_risk_population * 0.01)

    @api.depends("town_population", "county_previous_year_pci_quantity", "county_total_population")
    def _compute_previous_year_pci(self):
        for rec in self:
            if rec.county_total_population and rec.county_previous_year_pci_quantity:
                rec.town_previous_year_pci_quantity_estimation = math.ceil(rec.town_population / rec.county_total_population * rec.county_previous_year_pci_quantity)
            else:
                rec.town_previous_year_pci_quantity_estimation = 0

    # @api.depends("planned_pci_quantity", "town_theoretical_annual_pci_estimation")
    # def _compute_planned_pci_ratio(self):
    #     for rec in self:
    #         if rec.planned_pci_quantity:
    #             if rec.planned_pci_quantity / rec.town_theoretical_annual_pci_estimation > 0.9343:
    #                 rec.planned_pci_ratio_to_theoretical_quantity = 0.9343
    #             else:
    #                 rec.planned_pci_ratio_to_theoretical_quantity = rec.planned_pci_quantity / rec.town_theoretical_annual_pci_estimation
    #         else:
    #             rec.planned_pci_ratio_to_theoretical_quantity = 0

    @api.depends("planned_pci_ratio_to_theoretical_quantity")
    def _compute_high_risk_ratio(self):
        for rec in self:
            rec.planned_high_risk_population_management_ratio = (0.0036 * (math.exp(6.0274 * rec.planned_pci_ratio_to_theoretical_quantity)))

    @api.depends("planned_high_risk_population_management_ratio", "town_estimated_high_risk_population")
    def _compute_high_risk_quantity(self):
        for rec in self:
            if rec.town_estimated_high_risk_population:
                rec.planned_high_risk_population_management_quantity = math.ceil(rec.planned_high_risk_population_management_ratio * rec.town_estimated_high_risk_population)
            else:
                rec.planned_high_risk_population_management_quantity = 0

    @api.depends("planned_pci_ratio_to_theoretical_quantity", "town_theoretical_annual_pci_estimation")
    def _compute_pci_quantity(self):
        for rec in self:
            rec.predicted_pci_quantity_obtainable = math.ceil(rec.planned_pci_ratio_to_theoretical_quantity * rec.town_theoretical_annual_pci_estimation)

    @api.depends("planned_high_risk_population_management_quantity", "average_family_doctor_managed_high_risk_population")
    def _compute_family_doctor_count(self):
        for rec in self:
            if rec.average_family_doctor_managed_high_risk_population:
                rec.required_family_doctor_count = math.ceil(rec.planned_high_risk_population_management_quantity / rec.average_family_doctor_managed_high_risk_population)
            else:
                rec.required_family_doctor_count = 0

    @api.depends("required_family_doctor_count", "average_family_doctor_incentive_amount_per_month")
    def _compute_family_doctor_incentive_investment(self):
        for rec in self:
            rec.family_doctor_incentive_investment = rec.required_family_doctor_count * rec.average_family_doctor_incentive_amount_per_month * 12

    @api.depends("family_doctor_incentive_investment", "town_incentive_distribution_ratio", "family_doctor_incentive_distribution_ratio")
    def _compute_town_incentive_investment(self):
        for rec in self:
            if rec.family_doctor_incentive_distribution_ratio:
                rec.town_incentive_investment = rec.family_doctor_incentive_investment * rec.town_incentive_distribution_ratio / rec.family_doctor_incentive_distribution_ratio
            else:
                rec.town_incentive_investment = 0

    @api.depends("family_doctor_incentive_investment", "hospital_incentive_distribution_ratio", "family_doctor_incentive_distribution_ratio")
    def _compute_hospital_incentive_investment(self):
        for rec in self:
            if rec.family_doctor_incentive_distribution_ratio:
                rec.hospital_incentive_investment = rec.family_doctor_incentive_investment * rec.hospital_incentive_distribution_ratio / rec.family_doctor_incentive_distribution_ratio
            else:
                rec.hospital_incentive_investment = 0

    @api.depends("hospital_incentive_investment", "family_doctor_incentive_investment", "town_incentive_investment")
    def _compute_total_incentive_investment(self):
        for rec in self:
            rec.total_incentive_investment = rec.hospital_incentive_investment + rec.family_doctor_incentive_investment + rec.town_incentive_investment

    @api.depends("predicted_pci_quantity_obtainable", "town_previous_year_pci_quantity_estimation", "pci_medical_insurance_payment_limit", "pci_average_accounting_cost")
    def _compute_annual_increment_pci_revenue(self):
        for rec in self:
            rec.annual_increment_pci_revenue = (rec.predicted_pci_quantity_obtainable - rec.town_previous_year_pci_quantity_estimation) * (
                    rec.pci_medical_insurance_payment_limit - rec.pci_average_accounting_cost)

    @api.depends("annual_increment_pci_revenue", "total_incentive_investment")
    def _compute_annual_management_incremental_revenue(self):
        for rec in self:
            rec.annual_management_incremental_revenue_estimate = rec.annual_increment_pci_revenue - rec.total_incentive_investment

    sample = fields.Html(string="示意", compute="_compute_table", readonly=True, store=False)

    chart = fields.Text(string="示意图", compute="_compute_chat", readonly=False, store=True)

    @api.depends("pci_referral_incentive_amount", "follow_up_incentive_amount", "ecg_incentive_amount")
    def _compute_chat(self):


        x_data = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        y_data = [820, 932, 901, 934, 1290, 1330, 1320]
        html = Line().set_global_opts(
                tooltip_opts=opts.TooltipOpts(is_show=False),
                xaxis_opts=opts.AxisOpts(type_="category"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    axistick_opts=opts.AxisTickOpts(is_show=True),
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                ),
            ).add_xaxis(xaxis_data=x_data).add_yaxis(
                series_name="",
                y_axis=y_data,
                symbol="emptyCircle",
                is_symbol_show=True,
                label_opts=opts.LabelOpts(is_show=False),
            ).render_embed()

        for rec in self:
            rec.chart = '''<img src="//static/line.png" >'''
            print(rec.chart)

    @api.depends("pci_referral_incentive_amount", "follow_up_incentive_amount", "ecg_incentive_amount")
    def _compute_table(self):
        for rec in self:
            data = {
                "家医A": {
                    "患者数量": 100,
                    "月PCI上转": 1,
                    "月心电图次数": 100,
                    "月随访次数": 400
                },
                "家医B": {
                    "患者数量": 80,
                    "月PCI上转": 0,
                    "月心电图次数": 80,
                    "月随访次数": 200
                },
                "家医C": {
                    "患者数量": 50,
                    "月PCI上转": 0,
                    "月心电图次数": 30,
                    "月随访次数": 100
                },
                "家医D": {
                    "患者数量": 100,
                    "月PCI上转": 0,
                    "月心电图次数": 100,
                    "月随访次数": 400
                },
                "家医E": {
                    "患者数量": 60,
                    "月PCI上转": 0,
                    "月心电图次数": 20,
                    "月随访次数": 200
                },
                "家医F": {
                    "患者数量": 70,
                    "月PCI上转": 1,
                    "月心电图次数": 50,
                    "月随访次数": 200
                },
                "家医G": {
                    "患者数量": 90,
                    "月PCI上转": 2,
                    "月心电图次数": 90,
                    "月随访次数": 360
                },
                "家医H": {
                    "患者数量": 100,
                    "月PCI上转": 0,
                    "月心电图次数": 100,
                    "月随访次数": 400
                }
            }

            col_list = [" ", "家医A", "家医B", "家医C", "家医D", "家医E", "家医F", "家医G", "家医H"]
            row_list = ["患者数量",
                        "月PCI上转",
                        "月心电图次数",
                        "月随访次数",
                        "月PCI激励",
                        "月心电图激励",
                        "月随访激励",
                        "月激励总计"]
            json_data = []

            for row in row_list:
                row_dict = {}
                pci = 0
                ecg = 0
                follow = 0
                for col in col_list:
                    if col == " ":
                        row_dict[col] = row
                    elif row in ["患者数量",
                                 "月PCI上转",
                                 "月心电图次数",
                                 "月随访次数"]:
                        row_dict[col] = data[col][row]
                    elif row == "月PCI激励":
                        amount = round(data[col]["月PCI上转"] * rec.pci_referral_incentive_amount,1)
                        row_dict[col] = amount
                        data[col][row] = amount
                    elif row == "月心电图激励":
                        amount = round(data[col]["月心电图次数"] * rec.ecg_incentive_amount, 1)
                        row_dict[col] = amount
                        data[col][row] = amount
                    elif row == "月随访激励":
                        amount = round(data[col]["月随访次数"] * rec.follow_up_incentive_amount, 1)
                        row_dict[col] = amount
                        data[col][row] = amount
                    elif row == "月激励总计":
                        row_dict[col] = data[col]["月PCI激励"] + data[col]["月心电图激励"] + data[col]["月随访激励"]

                json_data.append(row_dict)

            # Convert JSON to HTML table
            html_table = '<table class="table table-bordered o_table"><tbody>'
            html_table += '<tr>' + ''.join(f'<th>{key}</th>' for key in json_data[0]) + '</tr>'
            html_table += ''.join('<tr>' + ''.join(f'<td><p>{value}</p></td>' for value in row.values()) + '</tr>' for row in json_data)
            html_table += '</tbody></table>'
            rec.sample = html_table
