from odoo import http
from odoo.http import request
import logging
import json
from ... import local_util
from ... import util
from ...util import Util
from werkzeug.utils import redirect
from pytz import timezone
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

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
    @http.route('/api/getRankData', methods=['POST', 'OPTIONS'], type="json", auth='public', csrf=False, cors="*")
    def getRankData(self, **kw):
        kw = request.httprequest.json
        if "phone_num" not in kw:
            return local_util.api_response('PARAM_ERROR')

        start_time = datetime.strptime(request.env["ir.config_parameter"].sudo().get_param('rank.start_time'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=8)
        end_time = datetime.strptime(request.env["ir.config_parameter"].sudo().get_param('rank.end_time'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=8)
        records = request.env['rank.recharge'].sudo().search(
            [('transaction_time', '>=', start_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('transaction_time', '<=', end_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])

        phone_num_amount_map = {}

        for item in records:
            phone_num = item['phone_num']
            transaction_amount = item['transaction_amount']
            transaction_time = item['transaction_time']
            action_type = item['action_type']

            if action_type == "储值退款":
                transaction_amount = -transaction_amount

            if phone_num in phone_num_amount_map:
                phone_num_amount_map[phone_num][0] += transaction_amount
                if transaction_time > phone_num_amount_map[phone_num][1] and action_type == "充值":
                    phone_num_amount_map[phone_num][1] = transaction_time
            else:
                phone_num_amount_map[phone_num] = [transaction_amount, transaction_time]

        # 对phone_num_amount_map按照transaction_amount和transaction_time从大到小排序
        sorted_phone_num_amount = sorted(phone_num_amount_map.items(), key=lambda x: (-x[1][0], x[1][1]))
        current_time = datetime.now() + timedelta(hours=8)

        if current_time < start_time:
            status = "未开始"
        elif current_time >= start_time and current_time <= end_time:
            status = "进行中"
        elif current_time > end_time:
            status = "已结束"
        ranklist = [{'phone_num': i[0], 'total_amount': i[1][0], 'last_recharge_time': i[1][1]} for i in sorted_phone_num_amount]

        user_rank = -1
        for r in ranklist:
            if kw['phone_num'] == r['phone_num']:
                user_rank = ranklist.index(r) + 1

        if user_rank <= 21 and user_rank > 0 and status == "已结束":
            if_win = True
        else:
            if_win = False

        res = {
            'status': status,
            'rank': ranklist[:21],
            'user_rank': user_rank,
            'if_win': if_win
        }
        return local_util.api_response(code="OK", data=res)

    @http.route('/api/insert_data', methods=['POST', 'OPTIONS'], type="json", auth='none', csrf=False, cors="*")
    def insert_data(self, **kw):
        kw = request.httprequest.json
        for i in kw["data"]:
            t_id = request.env['rank.recharge'].sudo().search([('transaction_serial_code', '=', i['transaction_serial_code'])]).id
            if not t_id:
                print(i)
                request.env['rank.recharge'].sudo().create(i)
        return "OK"
