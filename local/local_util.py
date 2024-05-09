import json
import decimal
from odoo.http import request
from datetime import date, time, datetime
from odoo.http import Response
from odoo import http
from functools import wraps
import uuid
import configparser
import os
import psutil

RESPONSE_CODE_LIST = {
    "ERR": (-1, "未知错误"),

    "OK": (0, "成功"),
    "ERR": (1, "错误"),

    "TOKEN_CHANGED": (2103, "登录环境改变"),
    "TOKEN_EXPIRED": (2104, "登录凭证已过期"),
    "TOKEN_TYPE_ERROR": (2105, "登录凭证类型错误"),
    "TOKEN_USER_ERROR": (2106, "无效的用户"),
    "TOKEN_USER_INVALID": (2107, "账号已禁用"),
    "USER_NOT_FOUND": (2108, "用户不存在或已封禁"),

    "DB_CONN_FAILED": (10, "数据库连接失败"),
    "SQL_ERROR": (11, "SQL错误"),

    "SMS_SEND_FAILED": (20, "短信发送失败"),

    "CODE403": (403, "无访问权限"),
    "CODE404": (404, "接口不存在"),
    "CODE405": (405, "方法不支持"),
    "CODE500": (500, "服务端异常"),

    "REQUEST_NUMBER_LIMIT": (1000, "请求次数超出限制"),
    "REQUEST_INTERVAL_LIMIT": (1001, "请求频率超出限制"),
    "REAUEST_NOT_JSON": (1002, "请求不是JSON格式"),

    "PARAM_NOT_FOUND": (1100, "参数不足"),
    "PARAM_TYPE_ERROR": (1101, "参数类型错误"),
    "PARAM_ERROR": (1102, "参数错误"),
    "PARAM_RANGE_ERROR": (1103, "参数范围错误"),
    "PARAM_FORMAT_ERROR": (1104, "参数格式错误"),
    "PARAM_MOBILE_ERROR": (1105, "手机号错误"),
    "PARAM_EMAIL_ERROR": (1106, "邮箱错误"),
    "PARAM_PHONE_ERROR": (1107, "电话错误"),
    "PARAM_TIMESTR_ERROR": (1108, "时间错误"),
    "PARAM_CODE_ERROR": (1109, "验证码错误"),
    "PARAM_CODE_INVALID": (1110, "验证码无效"),

    "DATA_EXIST": (2000, "数据已存在"),
    "DATA_NOT_FOUND": (2001, "数据不存在"),
    "DATA_NOT_CHANGE": (2002, "数据未改变"),
    "DATA_ERROR": (2003, "数据错误"),

    "TOKEN_NOT_FOUND": (2100, "缺少登录凭证"),
    "TOKEN_ERROR": (2101, "非法的登录凭证"),
    "TOKEN_INVALID": (2102, "登录凭证已失效"),

    "TOKEN_CHANGED": (2103, "登录环境改变"),
    "TOKEN_TYPE_ERROR": (2105, "登录凭证类型错误"),
    "TOKEN_USER_ERROR": (2106, "无效的用户"),
    "TOKEN_USER_INVALID": (2107, "账号已禁用"),
    "TOKEN_PWD_ERROR": (2108, "密码已被改变"),

    "USER_NOT_LOGIN": (2200, "用户未登录"),
    "USER_NOT_FOUND": (2201, "用户不存在"),
    "USER_INVALID": (2202, "无效的用户"),
    "USER_TYPE_ERROR": (2203, "用户类型错误"),
    "USER_PWD_ERROR": (2204, "用户密码错误"),
    "USER_PRIV_ERROR": (2205, "用户权限不足"),
    "USER_EXIST": (2206, "用户已存在"),

}


def config(key):
    # 从命令行中获取配置文件地址
    p = psutil.Process(os.getpid())
    for i in p.cmdline():
        if i.endswith(".cfg"):
            file = i
    # 创建配置文件对象
    con = configparser.ConfigParser()
    con.read(os.path.abspath(file), encoding='utf-8')
    item = con.get("smo", key)
    return item


def api_response(code, msg=None, data=None, **kwargs):
    code = str(code).upper()
    if code not in RESPONSE_CODE_LIST.keys():
        code = "ERR"
    if msg is None:
        msg = RESPONSE_CODE_LIST[code][1]
    if data is None:
        data = ""

    result = {"code": RESPONSE_CODE_LIST[code][0], "msg": msg, "data": data}
    result.update(**kwargs)
    return result


def check_params(check_list=None):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if check_list is not None:
                if hasattr(http.request, "jsonrequest"):
                    body = http.request.json
                else:
                    body = http.request.params
                for key in check_list:
                    if not key in body.keys():
                        return api_response('PARAM_ERROR')
                    else:
                        # 如果有值判断类型
                        if body[key] and check_list[key]:
                            if type(body[key]) != check_list[key]:
                                return api_response('PARAM_ERROR')
            return func(*args, **kwargs)

        return wrapper

    return decorate




def sync_data(self, pg_table, mq_table):
    mysql_query = """SELECT * from %s""" % (mq_table)
    self.env.cr.execute(mysql_query)
    mysql_res = self.env.cr.dictfetchall()

    # 以数据库名称为租户
    if mysql_res:
        if "tenant_code" in mysql_res[0]:
            mysql_res = [m for m in mysql_res if m["tenant_code"] == self.env.cr.dbname]
        # 只同步未删除的数据
        if "rows_state" in mysql_res[0]:
            mysql_res = [m for m in mysql_res if m["rows_state"] == "1"]

    if mysql_res:

        pg_query = """SELECT * from %s""" % (pg_table)
        self.env.cr.execute(pg_query)
        pg_res = self.env.cr.dictfetchall()

        # 以数据库名称为租户
        if pg_res:
            if "tenant_code" in pg_res[0]:
                pg_res = [p for p in pg_res if p["tenant_code"] == self.env.cr.dbname]

        for p in pg_res:
            # 覆盖更新
            update_list = []
            if_match = False
            for m in mysql_res:
                if p["o_id"] == m["id"]:
                    if_match = True
                    if_need_upadte = False
                    for key in p:
                        if key != "id" and key in m:
                            if m[key] != p[key]:
                                if_need_upadte = True
                                break;
                    if if_need_upadte:
                        for key in mysql_res[0]:
                            if key not in ["id", "cdt", "edt", "cman", "eman"]:
                                if type(m[key]) == str:
                                    update_list.append(""""%s" = '%s'""" % (key, m[key]))
                                elif type(m[key]) == int or type(m[key]) == float:
                                    update_list.append(""""%s" = %s""" % (key, m[key]))
                                elif type(m[key]) == datetime.datetime:
                                    update_list.append(""""%s" = '%s'""" % (key, m[key].strftime('%Y-%m-%d %H:%M:%S')))

                        set_str = " , ".join(update_list)
                        # self为空只能用sql更新数据
                        update_sql = """UPDATE %s SET %s WHERE id = %s """ % (pg_table, set_str, p["id"])
                        self.env.cr.execute(update_sql)
                        break;
                    mysql_res.remove(m)

            if not if_match:
                del_query = """DELETE from %s WHERE o_id = '%s'""" % (pg_table, p["o_id"])
                self.env.cr.execute(del_query)

        # mysql未匹配到的新增
        vals = []
        for m in mysql_res:
            append_dict = {"o_id": m["id"]}
            for key in mysql_res[0]:
                if key not in ["id", "cdt", "edt", "cman", "eman"]:
                    append_dict[key] = m[key]
            vals.append(append_dict)
        if vals:
            self.sudo().create(vals)

def del_user(self):
    del_user_query = """DELETE from smo_cust_user_info WHERE id = '%s'""" % (self.id)
    del_user_role_query = """DELETE from smo_cust_user_role_info WHERE user_id = '%s'""" % (self.id)
    self.env.cr.execute(del_user_query)
    self.env.cr.execute(del_user_role_query)


def sync_user_info(self,user_info):
    insert_dict = {
        "id": user_info["id"],
        "tenant_code": self.env.cr.dbname,
        "user_type_one": "employee", #默认员工
        "data_authority_type": "1", #TODO 目前默认全部
        "user_name": user_info["name"],
        "nick_name": user_info["name"],
        "user_state": "1",
        "nation_code": "86",
        "reg_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    col_list = ",".join(insert_dict.keys())
    val_list = ",".join(["'%s'" % (insert_dict[k]) for k in insert_dict])

    insert_sql = """INSERT INTO smo_cust_user_info (%s) VALUES (%s) ; """ % (col_list, val_list)
    print(insert_sql)
    self.env.cr.execute(insert_sql)

    uid = uuid.uuid4()
    insert_dict = {
        "id": uid,
        "tenant_code": self.env.cr.dbname,
        "user_id": user_info["id"],  # 默认员工
        "role_code": "code007"  # TODO 需要统一修改目前测试数据库暂定为code007
    }

    col_list = ",".join(insert_dict.keys())
    val_list = ",".join(["'%s'" % (insert_dict[k]) for k in insert_dict])

    insert_sql = """INSERT INTO smo_cust_user_role_info (%s) VALUES (%s) ; """ % (col_list, val_list)
    print(insert_sql)
    self.env.cr.execute(insert_sql)


def sync_dict_info(self, code, name, config):
    uid = uuid.uuid4()
    mysql_query = """SELECT * from smo_basic_dict_info WHERE "code" = '%s' and tenant_code = '%s' """ % (
        code, self.env.cr.dbname)
    self.env.cr.execute(mysql_query)
    mysql_res = self.env.cr.dictfetchall()

    if mysql_res:
        update_sql = """UPDATE smo_basic_dict_info SET "config" = '%s' WHERE code = '%s' and tenant_code = '%s' """ % (
            str(config).replace("\'", "\""), code, self.env.cr.dbname)
        print(update_sql)
        self.env.cr.execute(update_sql)
    else:
        insert_dict = {
            "id": uid,
            "tenant_code": self.env.cr.dbname,
            "code": code,
            "name": name,
            "config": str(config).replace("\'", "\""),
            "rows_state": "1"
        }
        insert_col_list = []
        for key in insert_dict:
            insert_col_list.append(""""%s" = '%s'""" % (key, insert_dict[key]))

        col_list = ",".join(insert_dict.keys())
        val_list = ",".join(["'%s'" % (insert_dict[k]) for k in insert_dict])
        insert_sql = """INSERT INTO smo_basic_dict_info (%s) VALUES (%s) ; """ % (col_list, val_list)
        print(insert_sql)
        self.env.cr.execute(insert_sql)


# TODO 动作节点里也有元数据
def get_metadata_list(rule_ids):
    rule_ids = ["'" + id + "'" for id in rule_ids]
    rule_ids_sql_str = "(" + ",".join(rule_ids) + ")"

    mysql_query = '''
    select *
    from smo_r_rule_decision_tree_node_config_info where
    rule_config_id in %s and tenant_code = '%s'
    ''' % (rule_ids_sql_str, request.env.cr.dbname)

    request.env.cr.execute(mysql_query)
    mysql_res = request.env.cr.dictfetchall()

    metadata_dict = {}
    for r in mysql_res:
        if r["node_condition"]:
            node_condition = json.loads(r["node_condition"])
            vpcs = [i["vpc"] for i in node_condition["items"]]
            if r["rule_config_id"] in metadata_dict:
                metadata_dict[r["rule_config_id"]].extend(vpcs)
            else:
                metadata_dict[r["rule_config_id"]] = vpcs
            metadata_dict[r["rule_config_id"]] = list(set(metadata_dict[r["rule_config_id"]]))

    return metadata_dict
