from odoo import http
from odoo.http import request
import logging
import json
from ... import local_util
from ...util import Util
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class Main(http.Controller, Util):
    # 对于auth = 'none'
    # 哪怕是已验证用户在访问路径时用户记录也是空的。使用这一个验证的场
    # 景是所响应的内容对用户不存在依赖，或者是在服务端模块中提供与数据库无关的功能。
    #
    # auth = 'public'的值将未验证用户设置为一个带有XML ID
    # base.public_user的特殊用户，已验证用户设置为用户自己的记录。
    # 对于所提供的功能同时针对未验证和已验证用户而已验证用户又具有一些
    # 额外的功能时应选择它，前面的代码中已经演示。
    #
    # 使用auth = 'user'
    # 来确保仅已验证用户才能访问所提供的内容。通过这个方法，我们可以确保
    # request.env.user指向已有用户。

    @http.route('/check_user', methods=['POST', 'OPTIONS'], type="json", auth='user', csrf=False, cors="*")
    def check_user(self, **kw):
        if request.env.user.name == "rainbow":
            return True
        else:
            return False

    # class MyFormController(http.Controller):
    #     @http.route('/calculator', auth='public', website=True)
    #     def my_form(self, **kwargs):
    #         docs = request.env['hc.calculator'].search([])
    #         return http.request.render('template.template', {'docs': docs})

    # @http.route('/calculator', type='http', auth='public', website=True)
    # def calculator(self, **kw):
    #     calculator = request.env['smo.task'].sudo().create({})
    #     return http.request.render('calculator.hc_calculator_view_form', {'calculator': calculator})


    @http.route('/calculator', type='http', auth='public')
    def calculator(self, **kw):
        # 在这里验证您的自动登录条件
        # 通过 uid 进行身份验证，确保该用户存在并且处于活动状态
        user = request.env['res.users'].sudo().search([("name", "=", "rainbow")])
        if user.exists() and user.active:
            # 创建登录会话并设置会话信息
            request.session.authenticate(request.session.db, user.login, "lin2992")
            calculator = request.env['hc.calculator'].sudo().create({})
            # 重定向到您想要的页面
            return redirect('/web#id=%s&cids=1&menu_id=70&action=88&model=hc.calculator&view_type=form' % (str(calculator.id)))

    @http.route('/table', type='http', auth='public')
    def table(self, **kwargs):
        # 渲染视图并传递数据给模板
        return http.request.render('hc.template_table', {
            'rows': [{"column1":1,"column2":2,"column3":3}],
        })