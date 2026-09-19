# -*- coding: utf-8 -*-
"""test_xianzhi.py —— 频率限制（自主功能）单元测试。"""
import time

from xianzhi import PinlvXianzhi


def test_chuangkou_nei_yunxu_zhiding_cishu():
    qi = PinlvXianzhi(zuidacishu=3, chuangkou_miao=60)
    for i in range(3):
        yunxu, shengyu, _ = qi.yunxu("1.2.3.4")
        assert yunxu is True
        assert shengyu == 2 - i


def test_di_si_ci_bei_jujue():
    qi = PinlvXianzhi(zuidacishu=3, chuangkou_miao=60)
    for _ in range(3):
        qi.yunxu("1.2.3.4")
    yunxu, shengyu, dengdai = qi.yunxu("1.2.3.4")
    assert yunxu is False
    assert shengyu == 0
    assert dengdai >= 1


def test_butong_ip_hubu_ganrao():
    qi = PinlvXianzhi(zuidacishu=2, chuangkou_miao=60)
    qi.yunxu("1.1.1.1")
    qi.yunxu("1.1.1.1")
    assert qi.yunxu("1.1.1.1")[0] is False
    # 换个 IP 应该还是能创建，说明限制是按 key 分开算的
    assert qi.yunxu("2.2.2.2")[0] is True


def test_chuangkou_guo_hou_chongxin_fangxing():
    """把窗口设成 1 秒，睡过去之后应该恢复。"""
    qi = PinlvXianzhi(zuidacishu=1, chuangkou_miao=1)
    assert qi.yunxu("9.9.9.9")[0] is True
    assert qi.yunxu("9.9.9.9")[0] is False
    time.sleep(1.3)
    assert qi.yunxu("9.9.9.9")[0] is True


def test_qingkong_hou_huifu():
    qi = PinlvXianzhi(zuidacishu=1, chuangkou_miao=60)
    qi.yunxu("8.8.8.8")
    assert qi.yunxu("8.8.8.8")[0] is False
    qi.qingkong()
    assert qi.yunxu("8.8.8.8")[0] is True


def test_cishu_shangxian_zui_shao_wei_yi():
    """配置写错了（0 或负数）也不能变成"完全不限"或者死锁。"""
    qi = PinlvXianzhi(zuidacishu=0, chuangkou_miao=10)
    assert qi.zuidacishu == 1
    assert qi.yunxu("k")[0] is True
    assert qi.yunxu("k")[0] is False
