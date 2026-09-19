# -*- coding: utf-8 -*-
"""
test_url_yanzheng.py —— 校验层单元测试（安全边界测试的一部分）。

对应实验要求：
    「非法协议、超长 URL、空输入、重复短码和未知短码有明确反馈」
"""
import pytest

from url_yanzheng import (
    guifan_hua_zhuji,
    jianyan_chang_url,
    jianyan_duanma,
    jianyan_youxiaoqi,
)

BAIMINGDAN = ["localhost", "127.0.0.1", "host.docker.internal"]


# ---------------- 长 URL ----------------

def test_zhengchang_http_url_tongguo():
    tongguo, _ = jianyan_chang_url("http://localhost:9001/demo.html", BAIMINGDAN)
    assert tongguo is True


def test_zhengchang_https_url_tongguo():
    tongguo, _ = jianyan_chang_url("https://127.0.0.1/a/b?c=1", BAIMINGDAN)
    assert tongguo is True


def test_kong_shuru_bei_jujue():
    tongguo, wen = jianyan_chang_url("", BAIMINGDAN)
    assert tongguo is False
    assert "空" in wen


def test_kongge_shuru_bei_jujue():
    tongguo, _ = jianyan_chang_url("     ", BAIMINGDAN)
    assert tongguo is False


def test_feizifuchuan_bei_jujue():
    # 前端要是传了 null 或者数字过来，不能直接 .strip() 崩掉
    for huai in (None, 123, [], {}):
        tongguo, _ = jianyan_chang_url(huai, BAIMINGDAN)
        assert tongguo is False


def test_meiyou_xieyi_bei_jujue():
    tongguo, wen = jianyan_chang_url("localhost:9001/demo.html", BAIMINGDAN)
    assert tongguo is False
    assert "协议" in wen


@pytest.mark.parametrize("huai_xieyi", [
    "ftp://localhost/a",
    "file:///c:/windows/win.ini",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
])
def test_weixian_xieyi_bei_jujue(huai_xieyi):
    """这几种协议拿去做短链跳板是真实的攻击面，必须拒。"""
    tongguo, _ = jianyan_chang_url(huai_xieyi, BAIMINGDAN)
    assert tongguo is False


def test_chaochang_url_bei_jujue():
    chang = "http://localhost/" + ("a" * 3000)
    tongguo, wen = jianyan_chang_url(chang, BAIMINGDAN, zuidachangdu=2048)
    assert tongguo is False
    assert "太长" in wen


def test_baimingdan_wai_yuming_bei_jujue():
    tongguo, wen = jianyan_chang_url("http://www.baidu.com/", BAIMINGDAN)
    assert tongguo is False
    assert "白名单" in wen


def test_weizao_qianzhui_de_yuming_bei_jujue():
    """
    反例：evil-localhost.com 的用户名部分是 localhost。
    如果白名单用 startswith 比对就会被蒙混过关，这里必须挡住。
    """
    tongguo, _ = jianyan_chang_url("http://evil-localhost.com/a", BAIMINGDAN)
    assert tongguo is False

    # 这种是真的子域名，应该放行（假设 localhost 有子域）
    tongguo2, _ = jianyan_chang_url("http://a.localhost/x", BAIMINGDAN)
    assert tongguo2 is True


def test_daxiee_zhuji_yie_tongguo():
    """URL 里大小写混着写很常见，白名单比对要归一化。"""
    tongguo, _ = jianyan_chang_url("HTTP://LOCALHOST:9001/a", BAIMINGDAN)
    assert tongguo is True


def test_guifanhua_zhuji_qu_kouhao():
    assert guifan_hua_zhuji("http://LocalHost:9001/a") == "localhost"
    assert guifan_hua_zhuji("不是url") == ""


# ---------------- 自定义短码 ----------------

def test_duanma_kong_biaoshi_zidong_shengcheng():
    tongguo, wen = jianyan_duanma("")
    assert tongguo is True and wen == ""


def test_duanma_zhengchang_tongguo():
    for hao in ("abc", "shiyan-03", "A_b-9", "x" * 32):
        tongguo, _ = jianyan_duanma(hao)
        assert tongguo is True, hao


def test_duanma_taiduan_bei_jujue():
    tongguo, wen = jianyan_duanma("ab")
    assert tongguo is False
    assert "3~32" in wen


def test_duanma_taichang_bei_jujue():
    tongguo, _ = jianyan_duanma("x" * 33)
    assert tongguo is False


@pytest.mark.parametrize("huai", ["有中文", "有 空格", "a/b", "a?b", "a#b", "a.b", "a@b"])
def test_duanma_feifa_zifu_bei_jujue(huai):
    tongguo, _ = jianyan_duanma(huai)
    assert tongguo is False


def test_duanma_baoliuzi_bei_jujue():
    for hao in ("rest", "health", "api", "admin"):
        tongguo, _ = jianyan_duanma(hao)
        assert tongguo is False


# ---------------- 有效期（自主功能） ----------------

def test_youxiaoqi_bukong_ji_shi_ling():
    assert jianyan_youxiaoqi("") == (True, 0, "")
    assert jianyan_youxiaoqi(None) == (True, 0, "")
    assert jianyan_youxiaoqi(0) == (True, 0, "")


def test_youxiaoqi_zhengchang():
    tongguo, tianshu, _ = jianyan_youxiaoqi(30, 365)
    assert tongguo is True and tianshu == 30


def test_youxiaoqi_chaoguo_shangxian_bei_jujue():
    tongguo, _, wen = jianyan_youxiaoqi(400, 365)
    assert tongguo is False
    assert "365" in wen


def test_youxiaoqi_fushu_bei_jujue():
    tongguo, _, _ = jianyan_youxiaoqi(-5, 365)
    assert tongguo is False


def test_youxiaoqi_feishuzi_bei_jujue():
    tongguo, _, _ = jianyan_youxiaoqi("三十天", 365)
    assert tongguo is False
