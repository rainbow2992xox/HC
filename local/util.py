import math
import requests
from . import local_util
import json
import time


class Util(object):
    def chunks(self, arr, m):
        n = int(math.ceil(len(arr) / float(m)))
        return [arr[i:i + n] for i in range(0, len(arr), n)]

    def getLabel(self, model, col):
        return [s[1] for s in model._fields[col].selection if s[0] == model[col]][0]

    def check_selection(self, field, id):
        for s in field.selection:
            if id == s[0]:
                return True
        return False

    def deleteDuplicate(self, li):
        temp_list = list(set([str(i) for i in li]))
        li = [eval(i) for i in temp_list]
        return li

    def check_datetime(self, dates):
        for date in dates:
            try:
                time.strptime(date, "%Y-%m-%d %H:%M:%S")
            except:
                return False
        return True

    def get_user_info(self, code):
        err, res = self.get_user_access_token(code)
        if err or not res:
            return (err, None)
        url = "https://api.weixin.qq.com/sns/userinfo"
        params = {
            "access_token": res['access_token'],
            "openid": res['openid'],
            "lang": "zh_CN"
        }
        r = requests.get(url, params=params)
        if r.status_code == 200:
            user_info = json.loads(r.content.decode("utf8"))
            user_info["access_token"] = res['access_token']
            if "errcode" not in user_info:
                return (None, user_info)
            else:
                return (r.content, None)
        else:
            return (r.content, None)

    def get_user_access_token(self, code):
        url = "https://api.weixin.qq.com/sns/oauth2/access_token"
        params = {
            "appid": local_util.config("appID"),
            "secret": local_util.config("appsecret"),
            "code": code,
            "grant_type": "authorization_code"
        }
        r = requests.get(url, params=params)
        if r.status_code == 200:
            result = r.json()
            if "errcode" not in result:
                return (None, result)
            else:
                return (result["errmsg"], None)
        else:
            return (r.json(), None)

    def creat_form_result(self, request, task_template, task):
        form_result_list = []
        for f in task_template.form_template_id:
            f_dict = {"form_template_id": f.id, "task_id": task._origin.id}
            form_result_list.append(f_dict)

        return request.env['smo.form.result'].sudo().create(form_result_list)
