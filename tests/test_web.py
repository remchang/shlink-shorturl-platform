# -*- coding: utf-8 -*-
"""
test_web.py —— Web 接口功能测试 + 安全边界测试。

全部跑在假 Shlink 上（见 conftest.py 的 JiaKehuduan），
所以「没装 Docker 的电脑也能 pytest -q 跑通」。
"""
import pytest


def _zhuang_yingyong(jia_kehuduan, cishu=20, baimingdan=None):
    """按指定参数造一个新的 app（给需要改配置的用例用）。"""
    from app import chuangjian_app
    from peizhi import Peizhi

    pz = Peizhi()
    pz.xianzhi_chuangjian_cishu = cishu
    pz.xianzhi_chuangjian_chuangkou_miao = 60
    if baimingdan is not None:
        pz.chang_url_baimingdan = baimingdan
    yingyong = chuangjian_app(peizhi_duixiang=pz, kehuduan=jia_kehuduan)
    yingyong.config["TESTING"] = True
    return yingyong


# ==================== 页面与健康 ====================

def test_shouye_ke_dakai(kehu):
    xiangying = kehu.get("/")
    assert xiangying.status_code == 200
    assert "短网址管理台" in xiangying.get_data(as_text=True)


def test_jiankang_jiekou(kehu):
    ti = kehu.get("/api/jiankang").get_json()
    assert ti["ok"] is True
    assert ti["web"] == "ok"
    assert ti["shlink"] == "ok"


def test_shlink_huai_de_shihou_jiankang_yie_baocuo(jia_kehuduan):
    jia_kehuduan.jiankang_hao = False
    kehu = _zhuang_yingyong(jia_kehuduan).test_client()
    ti = kehu.get("/api/jiankang").get_json()
    # Web 自己还是好的，但要把 Shlink 的问题暴露出来，方便排障
    assert ti["web"] == "ok"
    assert ti["shlink"] == "bad"


# ==================== 创建短链 ====================

def test_chuangjian_chenggong(kehu):
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/demo.html"
    })
    assert xiangying.status_code == 200
    ti = xiangying.get_json()
    assert ti["ok"] is True
    assert ti["duanma"]
    assert ti["duan_url"].startswith("http://localhost:8080/")


def test_chuangjian_dai_zidingyi_duanma(kehu):
    ti = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "shiyan03",
    }).get_json()
    assert ti["duanma"] == "shiyan03"


def test_duanma_chongfu_fanhui_409(kehu):
    kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "chongfu",
    })
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/b.html",
        "zidingyi_duanma": "chongfu",
    })
    assert xiangying.status_code == 409
    assert "占用" in xiangying.get_json()["xiaoxi"]


def test_youxiaoqi_chuandao_kehuduan(kehu, jia_kehuduan):
    kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "youxiao_tianshu": 7,
    })
    # 断言参数真的传下去了，不是只在界面上显示个控件
    assert jia_kehuduan.diaoyong_jilu[-1]["youxiao_tianshu"] == 7


def test_changshen_jingrong_xingshi(kehu):
    """前端传 application/x-www-form-urlencoded 也要能用。"""
    xiangying = kehu.post("/api/duanlian", data={
        "chang_url": "http://localhost:9001/form.html"
    })
    assert xiangying.status_code == 200


# ==================== 校验与错误分支 ====================

def test_kong_url_fanhui_400(kehu):
    xiangying = kehu.post("/api/duanlian", json={"chang_url": ""})
    assert xiangying.status_code == 400
    assert xiangying.get_json()["ok"] is False


def test_feifa_xieyi_fanhui_400(kehu):
    xiangying = kehu.post("/api/duanlian", json={"chang_url": "ftp://localhost/x"})
    assert xiangying.status_code == 400
    assert "协议" in xiangying.get_json()["xiaoxi"]


def test_baimingdan_wai_fanhui_400(kehu):
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://www.example.com/x"
    })
    assert xiangying.status_code == 400
    assert "白名单" in xiangying.get_json()["xiaoxi"]


def test_feifa_duanma_fanhui_400(kehu):
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "有中文",
    })
    assert xiangying.status_code == 400


def test_chaochang_youxiaoqi_fanhui_400(kehu):
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "youxiao_tianshu": 99999,
    })
    assert xiangying.status_code == 400


def test_api_key_wuxiao_shizhi_cuowu(jia_kehuduan):
    from shlink_kehuduan import ShlinkCuowu
    jia_kehuduan.yao_baocuo = ShlinkCuowu(401, "Invalid API key")
    kehu = _zhuang_yingyong(jia_kehuduan).test_client()
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html"
    })
    # 不能把 500 甩给用户，要给一句能照着修的话
    assert xiangying.status_code == 500
    assert "API Key" in xiangying.get_json()["xiaoxi"]


def test_shlink_bukeyong_fanhui_502(jia_kehuduan):
    from shlink_kehuduan import ShlinkCuowu
    jia_kehuduan.yao_baocuo = ShlinkCuowu(502, "连不上 Shlink")
    kehu = _zhuang_yingyong(jia_kehuduan).test_client()
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html"
    })
    assert xiangying.status_code == 502


# ==================== 列表与统计 ====================

def test_liebiao_kong(kehu):
    ti = kehu.get("/api/duanlian").get_json()
    assert ti["ok"] is True
    assert ti["qingdan"] == []


def test_liebiao_han_ziduan(kehu):
    kehu.post("/api/duanlian", json={"chang_url": "http://localhost:9001/a.html"})
    ti = kehu.get("/api/duanlian").get_json()
    assert len(ti["qingdan"]) == 1
    tiao = ti["qingdan"][0]
    for ziduan in ("duanma", "duan_url", "chang_url", "chuangjian_shijian",
                   "fangwen_cishu", "youxiaoqi_jieshu"):
        assert ziduan in tiao, ziduan


def test_tongji_jiekou(kehu):
    kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "tj001",
    })
    ti = kehu.get("/api/duanlian/tj001/tongji").get_json()
    assert ti["ok"] is True
    assert ti["chang_url"] == "http://localhost:9001/a.html"
    assert "an_laiyuan" in ti and "an_tian" in ti


def test_tongji_weizhi_duanma_404(kehu):
    xiangying = kehu.get("/api/duanlian/buzhidao/tongji")
    assert xiangying.status_code == 404


def test_shanchu(kehu):
    kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "shandiao",
    })
    assert kehu.delete("/api/duanlian/shandiao").status_code == 200
    assert kehu.get("/api/duanlian/shandiao/tongji").status_code == 404


def test_shanchu_bucunzai_404(kehu):
    assert kehu.delete("/api/duanlian/meiyou").status_code == 404


def test_huizong(kehu):
    for i in range(3):
        kehu.post("/api/duanlian", json={
            "chang_url": "http://localhost:9001/%d.html" % i
        })
    ti = kehu.get("/api/huizong").get_json()
    assert ti["zong_duanlian_shu"] == 3


# ==================== 自主功能：二维码 ====================

def test_erweima_fanhui_png(kehu):
    kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html",
        "zidingyi_duanma": "qrcode1",
    })
    xiangying = kehu.get("/api/erweima/qrcode1")
    assert xiangying.status_code == 200
    assert xiangying.mimetype == "image/png"
    # PNG 魔数，确认真是张图不是一段 JSON
    assert xiangying.get_data()[:8] == b"\x89PNG\r\n\x1a\n"


def test_erweima_bucunzai_404(kehu):
    assert kehu.get("/api/erweima/meiyou").status_code == 404


# ==================== 自主功能：频率限制 ====================

def test_pinlv_xianzhi_fanhui_429(jia_kehuduan):
    kehu = _zhuang_yingyong(jia_kehuduan, cishu=3).test_client()
    for i in range(3):
        assert kehu.post("/api/duanlian", json={
            "chang_url": "http://localhost:9001/%d.html" % i
        }).status_code == 200
    xiangying = kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/4.html"
    })
    assert xiangying.status_code == 429
    assert "频繁" in xiangying.get_json()["xiaoxi"]


def test_feifa_qingqiu_yie_ji_ru_xianzhi(jia_kehuduan):
    """非法请求也要计数，不然攻击者可以用垃圾请求白嫖配额。"""
    kehu = _zhuang_yingyong(jia_kehuduan, cishu=2).test_client()
    assert kehu.post("/api/duanlian", json={"chang_url": ""}).status_code == 400
    assert kehu.post("/api/duanlian", json={"chang_url": ""}).status_code == 400
    assert kehu.post("/api/duanlian", json={
        "chang_url": "http://localhost:9001/a.html"
    }).status_code == 429


# ==================== 安全边界：密钥不能外泄 ====================

def test_gongkai_peizhi_li_meiyou_api_key(kehu):
    ti = kehu.get("/api/peizhi").get_json()
    wenben = str(ti)
    assert "shlink_api_key" not in wenben
    assert "X-Api-Key" not in wenben
    # 只该暴露白名单和各项上限
    assert "chang_url_baimingdan" in ti


def test_qianmian_ye_meiyou_api_key(kehu):
    """整个首页的 HTML + JS 里都不该出现 Key。"""
    for lujing in ("/", "/static/qianduan.js", "/static/zhuti.css"):
        zhengwen = kehu.get(lujing).get_data(as_text=True)
        assert "X-Api-Key" not in zhengwen
        assert "X-Api-Key" not in zhengwen.replace("x-api-key", "")
        assert "ghp_" not in zhengwen


def test_weizhi_jiekou_404_bushi_wuran(kehu):
    xiangying = kehu.get("/api/buzhidaode/lujing")
    assert xiangying.status_code == 404
    assert xiangying.get_json()["ok"] is False
