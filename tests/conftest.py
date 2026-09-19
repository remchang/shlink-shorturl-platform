# -*- coding: utf-8 -*-
"""conftest.py —— 让测试能 import 到 web/ 下的模块。"""
import os
import sys

GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(GEN, "web")
if WEB not in sys.path:
    sys.path.insert(0, WEB)

import pytest  # noqa: E402


class JiaKehuduan:
    """
    假的 Shlink 客户端。测试不该依赖真的 Docker 容器起来，
    不然「没装 Docker 的电脑跑不了测试」——这不符合「可重复测试」。

    它只实现 web 层真正会调用的那几个方法，行为按 Shlink 5.1.6 的真实响应形状来。
    """

    def __init__(self, jiankang_hao=True):
        self.jiankang_hao = jiankang_hao
        self.yi_cunzai = set()          # 模拟已被占用的短码
        self.cundang = []               # 模拟已创建的短链
        self.diaoyong_jilu = []         # 记录调用，方便断言参数传对了没
        self.yao_baocuo = None          # 想模拟错误时塞一个 ShlinkCuowu

    def jiankang(self):
        if self.jiankang_hao:
            return True, "Shlink 状态：pass"
        return False, "连不上 Shlink"

    def chuangjian_duanlian(self, chang_url, zidingyi_duanma="", youxiao_tianshu=0,
                            biaoqian=None):
        from shlink_kehuduan import ShlinkCuowu
        if self.yao_baocuo:
            raise self.yao_baocuo

        self.diaoyong_jilu.append({
            "chang_url": chang_url,
            "zidingyi_duanma": zidingyi_duanma,
            "youxiao_tianshu": youxiao_tianshu,
        })

        if zidingyi_duanma and zidingyi_duanma in self.yi_cunzai:
            # 真实 Shlink 对自定义短码冲突返回 400
            raise ShlinkCuowu(400, "Provided short code is already in use")

        duanma = zidingyi_duanma or ("abc%03d" % (len(self.cundang) + 1))
        self.yi_cunzai.add(duanma)
        tiao = {
            "shortCode": duanma,
            "shortUrl": "http://localhost:8080/" + duanma,
            "longUrl": chang_url,
            "dateCreated": "2026-09-19T10:00:00+08:00",
            "visitsSummary": {"total": 0},
            "tags": [],
            "meta": {"isValid": True},
        }
        self.cundang.insert(0, tiao)
        return tiao

    def liebiao_duanlian(self, ye=1, meiye=20, paixu="dateCreated:DESC"):
        return {
            "shortUrls": {
                "data": self.cundang[(ye - 1) * meiye: ye * meiye],
                "pagination": {
                    "currentPage": ye,
                    "totalPages": max(1, (len(self.cundang) + meiye - 1) // meiye),
                    "totalItems": len(self.cundang),
                },
            }
        }

    def dan_tiao(self, duanma):
        from shlink_kehuduan import ShlinkCuowu
        for tiao in self.cundang:
            if tiao["shortCode"] == duanma:
                return tiao
        raise ShlinkCuowu(404, "Short URL not found")

    def fangwen_tongji(self, duanma, ye=1, meiye=20):
        self.dan_tiao(duanma)   # 不存在就先抛 404
        return {
            "visits": {
                "data": [
                    {"date": "2026-09-19T11:00:00+08:00", "referer": "http://localhost:9001/",
                     "userAgent": "Mozilla/5.0 test"},
                    {"date": "2026-09-19T11:05:00+08:00", "referer": None,
                     "userAgent": "curl/8.0"},
                ],
                "pagination": {"currentPage": 1, "totalPages": 1, "totalItems": 2},
            }
        }

    def shan_chu(self, duanma):
        self.dan_tiao(duanma)
        self.cundang = [t for t in self.cundang if t["shortCode"] != duanma]
        return True

    def qu_suoyou(self, zuiduo=100):
        return self.cundang[:zuiduo]


@pytest.fixture
def jia_kehuduan():
    return JiaKehuduan()


@pytest.fixture
def kehu(jia_kehuduan):
    """Flask 测试客户端，注入假 Shlink。"""
    from app import chuangjian_app
    from peizhi import Peizhi

    pz = Peizhi()
    # 测试里显式把风控窗口设小一点，方便验证 429
    pz.xianzhi_chuangjian_cishu = 20
    pz.xianzhi_chuangjian_chuangkou_miao = 60

    yingyong = chuangjian_app(peizhi_duixiang=pz, kehuduan=jia_kehuduan)
    yingyong.config["TESTING"] = True
    with yingyong.test_client() as c:
        yield c
