"""
微信通知封装，依赖 http_client.httpx_post
"""
import json
from typing import List, Optional

from app.core.http_client import httpx_post
from app.config import NOTIFY_SERVICE_URL


def notify_wechat(msg: str, strategy_type: str = 'other_service', touser: List[str] = None):
    """
    通过远程通知服务发送企业微信消息
    :param msg: 消息内容
    :param strategy_type: 策略类型（用于服务端选择应用）
    :param touser: 接收人列表，默认 ['@all']
    """
    if touser is None:
        touser = ['@all']

    payload = {
        "msg": msg,
        "strategy_type": strategy_type,
        "touser": touser,
        "channel": "weixin"
    }

    headers = {"Content-Type": "application/json"}
    resp = httpx_post(NOTIFY_SERVICE_URL, data=json.dumps(payload), headers=headers)
    print(resp, resp.status_code if resp else '无响应')

    if resp is None or resp.status_code != 200:
        print(f"通知发送失败，状态码: {resp.status_code if resp else '无响应'}")
    else:
        print(f"通知发送成功，响应: {resp.text}")
