# -*- encoding=utf8 -*-
__author__ = "admin"
import os
import sys
import time,random,re
PATH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PATH_DIR)
from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from airtest.cli.parser import cli_setup
from config.config import *
from config.judge import judge
from config.sendmsgdingding import senddingding


class TaoBao:

    def __init__(self):
        if not cli_setup():
            auto_setup(__file__, logdir=None, devices=[
                "Android://127.0.0.1:5309/127.0.0.1:62027?cap_method=JAVACAP&&ori_method=ADBORI&&touch_method=ADBTOUCH",
            ])
        self.p = AndroidUiautomationPoco(use_airtest_input=True, screenshot_each_action=False)
        self.redisdb = redis.Redis(host='192.168.25.143', port=6379)
        self.shop_list = []
        self.brand_list = []
        self.reg = re.compile("(.*?)(天猫店)")
        self.reg1 = re.compile("信誉\d+")
        self.callback_res = {
            "shop_name": "",
            "t_m": ""
        }

    def tb_click(self):
        tb = self.p("手机淘宝")
        if tb:
            tb.click()

    def search_flag(self):
        login = self.p(text="亲，欢迎登录")

        a = self.p("android.widget.HorizontalScrollView")
        b = self.p("com.taobao.taobao:id/edit_del_btn")
        c = self.p("com.taobao.taobao:id/searchEdit")
        s = self.p("android.widget.LinearLayout").offspring("com.taobao.taobao:id/sv_search_view").child(
            "android.widget.FrameLayout").child("android.widget.FrameLayout").child("android.widget.FrameLayout").child(
            "android.widget.FrameLayout")
        if login:
            try:
                self.p("返回").wait(3.0).click()
            except Exception as e:
                keyevent("BACK")
                print(e)
        if a:
            a.wait(5.0).click()

        if b:
            b.wait(5).click()
        if c:
            c.wait(5).click()

        if s:
            s.wait(10).click()

    def text_input(self, a):
        self.search_flag()
        text(a, search=True)
        sleep(3)
        self.shop_click()

    def shop_click(self):
        shop = self.p(text="店铺")
        print("123")
        if shop:
            print("456")
            shop.wait(10).click()

        sleep(3)

    def data_parse(self, key):
        self.text_input(key)
        num = 0
        while num < 5:
            a = self.p("com.taobao.taobao:id/libsf_srp_header_list_recycler").child('android.widget.LinearLayout')
            x_y_list = []
            print(len(a))
            if len(a) > 0:
                for i in a:
                    shop = i.child("com.taobao.taobao:id/fl_top")
                    if shop:
                        shop_name = shop.attr("desc")
                        x_y = i.child("com.taobao.taobao:id/fl_top").attr("pos")
                        print('第一次拿到的值：', shop_name)
                        result = self.reg.findall(shop_name)
                        result1 = self.reg1.findall(shop_name)
                        if result:
                            shop_name = result[0]
                        else:
                            if result1:
                                shop_name = shop_name.replace(result1[0], '')
                                shop_name = (shop_name, '')

                            else:
                                shop_name = (shop_name, '')
                        if shop_name not in self.shop_list:
                            self.shop_list.append(shop_name)
                            print("处理后的值：", shop_name[0])
                            if shop_name[0] == key:
                                self.callback_res['shop_name'] = shop_name[0]
                                self.callback_res['t_m'] = shop_name[1]
                                break
                        print(x_y)
                        x_y_list.append(x_y)
                try:
                    self.p.swipe(x_y_list[-1], x_y_list[0], duration=0.5)
                except Exception as e:
                    print('滑动出错', e)
                sleep(1)
                num += 1
            else:
                break

    def back_search(self):

        back1 = self.p("转到上一层级")
        back2 = self.p("com.taobao.taobao:id/btn_go_back")
        if back1:
            back1.wait(5).click()
            if back2:
                back2.wait(5).click()

    def run(self):
        # self.get_brand()
        try:
            # 开始键入搜索
            while True:
                key = self.redisdb.spop("douyin_v")
                print(key.decode("utf8"))
                self.data_parse(key)
                self.back_search()
                print(self.shop_list)
                self.save_msq()
                self.shop_list = []
            pass
        except Exception as e:
            print("tabao爬虫出错： {}".format(e))


    def save_msq(self):
        tup = '(`shop_name`, `tai_mao`)'
        for i in self.shop_list:
            search_res = con.search_msg_mysql(table_name, search_name, i[0])
            if search_res:
                continue
            else:
                con.add_msg_mysql(table_name, tup, i)


if __name__ == '__main__':
    spider_msg = 'spider_msg'
    spider_msg_id = 'spider_id'
    table_name = 'tao_bao'
    search_name = "shop_name"
    con = ConfigContent1()
    tb = TaoBao()
    tb.run()