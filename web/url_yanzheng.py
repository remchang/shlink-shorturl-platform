# -*- coding: utf-8 -*-
"""
url_yanzheng.py —— 长 URL 与自定义短码的校验。

这是「自己的规则」而不是 Shlink 的规则。Shlink 支持的协议比本实验要求宽
（比如 ftp、mailto），实验要求只有 http/https 且域名在白名单内，
所以这一层必须由我们自己的接口强制执行。

返回统一用 (是否通过, 错误提示) 二元组，调用方不用记异常类型。
"""
import re
from urllib.parse import urlparse

# 只允许这两种协议。javascript: data: vbscript: 这类一律拒掉——
# 短链服务被拿去做 XSS / 钓鱼跳板是真实存在的事故。
YUNXU_XIEYI = ("http", "https")

# 自定义短码：3~32 位，只放字母数字和 - _ 。
# 不允许 / ? # 这些，否则会和路由打架；不允许中文，避免不同客户端编码不一致。
DUANMA_ZHENGZE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

# 一批明确要拒绝的短码，防止和 Shlink 自己的 REST 路径撞车
BAOLIU_DUANMA = {
    "rest", "health", "api", "admin", "static", "favicon.ico", "metrics",
}


def guifan_hua_zhuji(chang_url):
    """
    从 URL 里取出小写的 host（不含端口）。

    为什么单独拆出来：白名单是按域名比对的，但用户可能写成
    HTTP://LocalHost:9001/a 这种大小写混杂的形式，直接 startswith 比对会漏。
    """
    try:
        jiexi = urlparse(chang_url)
    except ValueError:
        return ""
    if not jiexi.hostname:
        return ""
    return jiexi.hostname.lower()


def jianyan_chang_url(chang_url, baimingdan, zuidachangdu=2048):
    """
    校验长 URL。返回 (True, "") 表示通过。

    按「先便宜后贵」的顺序查：类型 → 空 → 长度 → 协议 → 主机 → 白名单。
    """
    # ① 类型：前端传过来的可能是数字、null，不能直接 .strip()
    if chang_url is None or not isinstance(chang_url, str):
        return False, "长网址必须是字符串"

    qu_kong = chang_url.strip()
    if not qu_kong:
        return False, "长网址不能为空"

    # ② 长度
    if len(qu_kong) > zuidachangdu:
        return False, "长网址太长（最多 %d 个字符，当前 %d）" % (
            zuidachangdu,
            len(qu_kong),
        )

    # ③ 解析
    try:
        jiexi = urlparse(qu_kong)
    except ValueError:
        return False, "长网址格式不对，没法解析"

    # ④ 协议
    xieyi = (jiexi.scheme or "").lower()
    if xieyi not in YUNXU_XIEYI:
        if not xieyi:
            return False, "长网址要带协议头，例如 http:// 或 https://"
        return False, "只允许 http / https 协议，不支持 %s" % xieyi

    # ⑤ 主机名
    zhuji = jiexi.hostname
    if not zhuji:
        return False, "长网址里没有解析出主机名"

    # ⑥ 白名单。注意这里用「等于或子域名」比对，不用 startswith，
    #    否则 evil-localhost.com 会被 127.0.0.1 那种规则蒙混过关。
    zhuji_xiaoxie = zhuji.lower()
    for tiaomu in baimingdan:
        if zhuji_xiaoxie == tiaomu or zhuji_xiaoxie.endswith("." + tiaomu):
            return True, ""
    return False, "域名 %s 不在白名单内（本实验只允许本地/授权目标）" % zhuji


def jianyan_duanma(duanma):
    """
    校验自定义短码。空字符串表示「不自定义，让 Shlink 自己生成」，算通过。
    """
    if duanma is None:
        return True, ""
    if not isinstance(duanma, str):
        return False, "自定义短码必须是字符串"

    qu_kong = duanma.strip()
    if not qu_kong:
        # 没填就是让后端自动生成
        return True, ""

    if not DUANMA_ZHENGZE.match(qu_kong):
        return False, "自定义短码只能 3~32 位，字符限 A-Z a-z 0-9 - _"

    if qu_kong.lower() in BAOLIU_DUANMA:
        return False, "短码 %s 是系统保留字，换一个" % qu_kong

    return True, ""


def jianyan_youxiaoqi(tianshu, zuida_tianshu=365):
    """
    校验有效期天数（自主功能）。返回 (通过, 天数或0, 提示)。
    0 表示不设有效期。
    """
    if tianshu is None or tianshu == "" or tianshu == 0:
        return True, 0, ""

    try:
        zhengshu = int(tianshu)
    except (TypeError, ValueError):
        return False, 0, "有效期必须是整数天数"

    if zhengshu < 0:
        return False, 0, "有效期不能是负数"
    if zhengshu == 0:
        return True, 0, ""
    if zhengshu > zuida_tianshu:
        return False, 0, "有效期最多 %d 天（实验规则，防止建超长期短链）" % zuida_tianshu

    return True, zhengshu, ""
