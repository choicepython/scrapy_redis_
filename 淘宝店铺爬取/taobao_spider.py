# -*- coding: utf-8 -*-
import os
import sys
import re
import asyncio
import datetime
from urllib.parse import quote
from fake_useragent import UserAgent
import requests
import pymysql
import time, random
import json


def environment():
    return {'SERVERUSER': 'scapy', 'SERVERHOST': '47.99.154.157', 'SERVERDB': 'scapy', 'SERVERPORT': 39003,
            'SERVERPASSWD': 'FtBYKJJNLf7xY2BW', 'SERVERCHARSET': 'utf8mb4'}


class ConfigContent1(object):
    def __init__(self):
        mysqldb = environment()

        self.mysqldb = pymysql.connect(host=mysqldb['SERVERHOST'], port=mysqldb['SERVERPORT'],
                                       user=mysqldb['SERVERUSER'], password=mysqldb['SERVERPASSWD'],
                                       db=mysqldb['SERVERDB'], )
        self.cur = self.mysqldb.cursor()

    def get_cursor(self):
        cur = self.mysqldb.cursor()
        return cur

    def close_cur(self):
        try:
            self.cur.close()
        except Exception as e:
            print("关闭游标错误:{}".format(e))
            pass

    def create_tb(self, table_name, tum):
        """
        :param table_name: 表名
        :param tum: str类型,字符串内嵌元组:字段名和类型
        "( `id` INT NOT NULL AUTO_INCREMENT, `company` VARCHAR(50) NOT NULL, `com_xcx` VARCHAR(50) NOT NULL, PRIMARY KEY (`id`) )"
        :return:
        """
        cur = self.get_cursor()
        exist = self.table_exists(cur, table_name)
        if not exist:
            try:
                sql = "CREATE TABLE `{}`{}".format(table_name, tum)
                print(sql)
                cur.execute(sql)  # 执行sql
                print('创建成功')
            except Exception as e:
                print('创建失败', str(e))
            finally:
                self.close_cur()  # 关闭游标
                pass
        else:
            print("该表已创建")

    def add_msg_mysql(self, table_name, tup, *args):
        """
        INSERT INTO `douyin_xcx` (`id`, `company`, `com_xcx`) VALUES (NULL, '聚焦网络', '聚焦云名片')
        :param table_name:
        :param tup: str类型，字符串内嵌元组
        "(`id`, `company`, `com_xcx`)"
        :param args:元组：要添加字段的值
        :return:
        """
        sql = "INSERT INTO `{}` {} VALUES ".format(table_name, tup)
        sql = sql + "{}".format(*args)
        print(sql)
        try:
            # 本地数据库  留作备份
            self.cur.execute(sql)
            self.mysqldb.commit()
            print('add over~')
        except Exception as e:
            print("数据插入出错：{}".format(e))

    def add_many_msg(self, table_name, tup, ls):
        sql = f"INSERT INTO `{table_name}` {tup} VALUES (%s,%s,%s)"
        print(ls)
        try:
            print(sql)
            self.cur.executemany(sql, ls)
            self.mysqldb.commit()
            print('add many over~')
            time.sleep(random.random())
            self.mysqldb.close()
        except Exception as e:
            print(f"批量插入错误{e}")

    def del_msg_mysql(self, table_name, id):
        """
        DELETE FROM `test`.`douyin_xcx` WHERE `id` = '2'
        :param table_name:
        :param id:  通过 数据库自增id来删除行信息
        :return:
        """
        delete = "delete  from  `{}`  where id = '{}'".format(table_name, id)
        cur = self.get_cursor()
        try:
            cur.execute(delete)
            self.mysqldb.commit()
            time.sleep(1)
            print('del over! ', id)
        except Exception as e:
            print("数据删除错误：{}".format(e))

    def search_msg_mysql(self, table_name, name=None, value=None):
        """
        :param table_name:
        :param name: 字段名
        :param value: 字段值
        :return:
        """
        try:

            if name and value:
                sele = "select * from `{}`  where {} = '{}'".format(table_name, name, value)
                self.cur.execute(sele)
                result = self.cur.fetchall()
                if result:
                    return result
                time.sleep(1)

            elif not name or value:
                sele = "select * from `{}`".format(table_name)
                self.cur.execute(sele)
                result = self.cur.fetchall()
                if result:
                    return result
        except Exception as e:
            print("错误", e)

    def table_exists(self, cur, table_name):
        sql = "show tables;"
        cur.execute(sql)
        tables = cur.fetchall()
        # (('check_comp',), ('check_douyin_xcx',), ('douyin_xcx',), ('wechat_s',))
        reg = re.compile('(\'.*?)\'')
        table_list = reg.findall(str(tables))
        # ["'check_comp", "'check_douyin_xcx", "'douyin_xcx", "'wechat_s"]
        table_list = [re.sub("'", '', i) for i in table_list]
        # ['check_comp', 'check_douyin_xcx', 'douyin_xcx', 'wechat_s']
        if table_name in table_list:
            return 1
        else:
            return 0

    def parsing_mysql_content(self, content):
        # 将单引号转换成 双引号
        contents = content.replace("'", '"')
        # 将字符串转换为 字典格式
        contentss = json.loads(contents)
        return contentss


class TaoBao:
    def __init__(self):

        self.cookies = ''
        self.refer = ''
        self.flag = False
        self.sign = ''
        self.nowTime = datetime.datetime.now().strftime('%Y%m%d')
        self.proxy = ''
        # self.wd = wd
        self.brand_list = []
        self.save_data_list = []
        self.timeout = False
        self.ua = UserAgent()
        self.headers = {
            "user-agent": self.ua.random,
            'cookie': self.cookies,
            'referer': self.refer
        }
        self.url = "https://shopsearch.taobao.com/search?q={kw}&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_{date}&ie=utf8&s={pn}"

        self.reg = re.compile("亲，小二正忙，滑动一下马上回来")
        self.reg1 = re.compile('g_page_config = (.*?);\s+g_srp_loadCss')
        self.again_key = []
        self.data_list = []
        pass

    def data_spider(self, i, pn):
        # global ip_ls
        # if not ip_ls:
        #     tao_bao_ip(ip_ls)
        # ip = ip_ls[0].strip()
        # ip_ls = ip_ls[1:]
        # print("当前ip：", ip)
        # proxies = {
        #     'http': 'http://' + ip,
        #     'https': 'https://' + ip
        # }
        # params = {'q': self.wd,
        #         'js': '1',
        #         'initiative_id': 'staobaoz_20200221',
        #         'ie': 'utf8'}
        self.headers['cookie'] = self.cookies
        self.headers['referer'] = self.refer
        print('self.refer', self.refer)
        r = requests.get(self.url.format(kw=quote(i), date=self.nowTime, pn=str(pn * 20)), headers=self.headers,
                        timeout=8)    # proxies=proxies,
        # proxies=proxies,
        if r.status_code == 200:
            text = r.content.decode(r.apparent_encoding)
            print(r.cookies)
            back_or_no = self.reg.findall(text)
            data = self.reg1.findall(text)
            self.refer = r.url
            if back_or_no:
                print("当前cookie已失效")
                self.timeout = True
                return None
                # self.cookies = input("输入新的cookie：")
                # self.refer = input("输入新的refer：")
                # self.headers['cookie'] = self.cookies
                # self.headers['referer'] = self.refer
                # return self.data_spider(i, pn)

            if data:
                print("=" * 100)
                json_data = json.loads(data[0])
                mods = json_data["mods"]
                if "shoplist" in mods:
                    shop_list = mods["shoplist"]
                    if "data" in shop_list:
                        shop_items = shop_list.get("data").get("shopItems")
                        print(len(shop_items))
                        if shop_items:
                            for shopItem in shop_items:
                                # 店铺
                                title = shopItem["title"]
                                # 店铺链接
                                shopUrl = "https:" + shopItem["shopUrl"]
                                # 是否为天猫旗舰店标识
                                shopIcon = shopItem["shopIcon"].get("title")
                                if not shopIcon:
                                    shopIcon = ""
                                tup = (title, shopUrl, shopIcon)
                                self.data_list.append(tup)
                                print(
                                    "title :{}'\n'shopUrl: {} '\n'shopIcon:{}".format(title, shopUrl, shopIcon))

                                self.save_data_list.append(tup)

                    else:
                        print("搜索页没有任何结果")
                        self.flag = True
            else:
                print("页面无内容", r.text)
                self.timeout = True

    def save_msq(self, data):
        con = ConfigContent1()
        tup = '(`shop_name`, `shop_url`, `tai_mao`)'
        # search_res = con.search_msg_mysql(table_name, search_name, data[0])
        # if search_res:
        #     print("跳过插入")
        # else:
        #     con.add_msg_mysql(table_name, tup, data)
        con.add_many_msg(table_name, tup, data)
        time.sleep(random.randint(1, 3))

    def run(self):
        self.cookies = 'hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; t=4ee589cbdf84f9c22e6028420193d8f1; cna=835WFiASHHUCAT2QIkpC45Bo; sgcookie=Q%2BAljdnUDf6VytEKA9Hj; uc3=id2=UNN9dgBrypr9hg%3D%3D&nk2=06uUNygXxr0%3D&lg2=UIHiLt3xD8xYTw%3D%3D&vt3=F8dBxdz3oVZwju5CR3g%3D; lgc=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; uc4=id4=0%40UgQ1KBe7v%2BBPdJ0t0h%2BG3ruYvaNS&nk4=0%400RBMkrnbwaCWx5BY3s1yaMyGXw%3D%3D; tracknick=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; _cc_=UtASsssmfA%3D%3D; tg=0; tfstk=b#BvNBH21AAHZFY61GTBVlfdiRwKOZLKMmJS5sQbPE+H0TMCGiVzAxcAlYi/+K1f==; mt=ci=6_1; enc=Z5UDQd9SOZD%2Bc0QwlkL3eFcZmQKH190UEUNfT63da4gEDVe6KrAgOt60tvsYzY40xue0HFNDz3Gkz57YGJmwPg%3D%3D; v=0; uc1=cookie14=UoTUOLbPV4ZuKg%3D%3D; cookie2=15501585f9e6f3d6ddfbd4b4a38da810; _tb_token_=b75b601bbe38; JSESSIONID=E989744A9C65376D236432F7210994F0; isg=BO3tuCl-Tx8lHSjA48dBxK9s_IlnSiEcDrRZny_yKQTzpg1Y95ox7Dt0lHpAPTnU; l=dBQNSYhgq9IHPoZsBOCanurza77OSIRYYuPzaNbMi_5dp6T6Dm7Oo-qC8F96VjWft68B4dH2-sp9-etkZs8ZBy8U-dWMKDc.'
        self.refer = 'https://shopsearch.taobao.com/search?ie=utf8&initiative_id=staobaoz_20200221&js=1&q=%E5%A5%88%E7%B1%B3%E7%88%B1&suggest=0_2&_input_charset=utf-8&wq=%E5%A5%88%E7%B1%B3&suggest_query=%E5%A5%88%E7%B1%B3&source=suggest'
        import redis

        redisdb = redis.Redis(host='127.0.0.1', port=6379)
        while True:
            res = redisdb.spop("taobao")
            print(res.decode("utf8"))
            if not res:
                print("品牌遍历完成")
                break
            pn = 0
            while pn <= 20:

                print(f"当前页数{pn}")
                self.save_data_list = []
                try:
                    self.data_spider(res, pn)
                except Exception as e:
                    print(f"访问错误{e}")
                pn += 1
                # if pn == 1:
                #     if self.timeout:
                #         break
                        # self.timeout = False
                        # self.cookies = input("输入cookies：")
                if self.timeout:
                    break
                if self.save_data_list:
                    self.save_msq(self.save_data_list)
                else:
                    break

            if self.timeout:
                break

            print(f"参数{res}爬取完成")


def tao_bao_ip(ls):
    url = "http://route.xiongmaodaili.com/xiongmao-web/api/glip?secret=a65e2f219d2eed89cf4c066f8ff255ca&orderNo=GL20200221192644uB3nzcqo&count=10&isTxt=1&proxyType=1"
    r = requests.get(url)
    print(r.status_code)
    if r.status_code == 200:
        print(r.text.strip(), type(r.text.strip()))
        ips = r.text.strip()
        ip_list = ips.split('\n')
        ls += ip_list
        return ip_list


def get_free_ip(ls):
    with open('E:\PycharmProjects\\test02\代理ip\proxies.txt', "r", encoding='utf8') as f_r:
        ips = f_r.readlines()
        for i in ips:
            ip = i.split(",")[-1]
            print(ip)
            if ip:
                ls.append(ip.strip())


if __name__ == '__main__':
    spider_msg = 'spider_msg'
    spider_msg_id = 'spider_id'
    table_name = 'tao_bao'
    table_name1 = 'tao_bao_cookie'
    cookie_tup = '(`cookie`, `valid`)'
    search_name = "shop_name"

    ip_ls = []
    while True:
        t_b = TaoBao()
        t_b.run()
        print('进行休眠30分钟')
        print(time.localtime())
        time.sleep(30*60)

    # cookie = "thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; sgcookie=Q69w3TCSSIV1A0MXu7b6; uc3=nk2=ogVZTHsMoDEt1SMX&vt3=F8dBxdz0xkkgWiaszQ8%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UU27LTb4AXoiAA%3D%3D; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; uc4=nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvYJ9c%2BV9I8%3D&id4=0%40U2%2F8m%2FP6up3dR%2FWCyemFJJyG9IvL; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; _cc_=VT5L2FSpdA%3D%3D; tg=0; enc=0hS6oWCaJ8sQf63WozTa37bVyJjh1eSQuQ7taG5wphm97Es2PJo8gEQLDZtKKA2peIsvE1Ydg1Wp5%2FYXifgZdg%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; v=0; cookie2=142ce5e2cdd32b91bde234973ac3ea51; _tb_token_=31378e1733975; x5sec=7b2274616f62616f2d73686f707365617263683b32223a223863613238323430383339636366323237666334646362396664376230346631434f434a7266494645497a476a71696e386f474957526f4d4d6a55354d6a6b334f5441324f447332227d; uc1=cookie14=UoTUO8kOHKzcVA%3D%3D; alitrackid=www.taobao.com; lastalitrackid=www.taobao.com; JSESSIONID=A65EDCB128B0817485AF9D0606481B10; isg=BAUFc7kd9883VdORioZFbSjZFEE_wrlUSv5vdgdqGjxLnicQzRf4JNU4qMJo3tEM; l=cBxi3DBlQUuyHh33BOfaourza77T4IRbzsPzaNbMiICPO4Ce5HMhWZVite8wCnGVK6qH-3uRJbTbB-LlDyCq3Tt-CLnXmp5.."
    # cookie='hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; t=4ee589cbdf84f9c22e6028420193d8f1; cookie2=1efb8c800394144cb4085d2ca9442cb0; _tb_token_=3e89d6813ef63; _samesite_flag_=true; cna=835WFiASHHUCAT2QIkpC45Bo; v=0; sgcookie=Q%2BAljdnUDf6VytEKA9Hj; unb=3303297383; uc3=id2=UNN9dgBrypr9hg%3D%3D&nk2=06uUNygXxr0%3D&lg2=UIHiLt3xD8xYTw%3D%3D&vt3=F8dBxdz3oVZwju5CR3g%3D; csg=a07a7a77; lgc=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; cookie17=UNN9dgBrypr9hg%3D%3D; dnk=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; skt=0a42054996863be9; existShop=MTU4MjExMDkyOA%3D%3D; uc4=id4=0%40UgQ1KBe7v%2BBPdJ0t0h%2BG3ruYvaNS&nk4=0%400RBMkrnbwaCWx5BY3s1yaMyGXw%3D%3D; tracknick=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; _cc_=UtASsssmfA%3D%3D; tg=0; _l_g_=Ug%3D%3D; sg=%E3%81%8234; _nk_=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; cookie1=BxNYK13uN2MgQxOIBZj%2B184MR3IqAWOHVOltyZP8bjE%3D; alitrackid=login.taobao.com; lastalitrackid=login.taobao.com; tfstk=b#BvNBH21AAHZFY61GTBVlfdiRwKOZLKMmJS5sQbPE+H0TMCGiVzAxcAlYi/+K1f==; uc1=cookie16=WqG3DMC9UpAPBHGz5QBErFxlCA%3D%3D&cookie21=URm48syIYn73&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&existShop=false&pas=0&cookie14=UoTUOLIrkYGFhQ%3D%3D&tag=8&lng=zh_CN; mt=ci=6_1; enc=%2FlHcGGMvpgBEceeIGEuycvOHRlQArfVLE3HKftzRENJdJvMRKUgRQVauVVUOeMsE0jNN9RKI0mYr1uNZJPNrPg%3D%3D; x5sec=7b2274616f62616f2d73686f707365617263683b32223a2263336533346333396264336631663730393562636532346334343964333732624350697874504946454d336670736950317247587767456144444d7a4d444d794f54637a4f444d374d513d3d227d; l=cBQNSYhgq9IHPVO2BOfwKurza77OoCOfCsPzaNbMiICPOpCe5nW5WZVQENTwCnGVLsspR3Jt3efYB0LT0y4EhxywiAxk-Ic1.; isg=BGdnSbBa9TOfxHISVWGrVsFi9psx7DvOMApjLTnRg_YkKI_qQb4QH6FqSii2wBNG; JSESSIONID=1198A7D76907E66B29CC23DFFCE43598'
    # cookie = 'thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; sgcookie=Q69w3TCSSIV1A0MXu7b6; uc3=nk2=ogVZTHsMoDEt1SMX&vt3=F8dBxdz0xkkgWiaszQ8%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UU27LTb4AXoiAA%3D%3D; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; uc4=nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvYJ9c%2BV9I8%3D&id4=0%40U2%2F8m%2FP6up3dR%2FWCyemFJJyG9IvL; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; _cc_=VT5L2FSpdA%3D%3D; tg=0; enc=0hS6oWCaJ8sQf63WozTa37bVyJjh1eSQuQ7taG5wphm97Es2PJo8gEQLDZtKKA2peIsvE1Ydg1Wp5%2FYXifgZdg%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; x5sec=7b2274616f62616f2d73686f707365617263683b32223a223266393037646161373530666539663665393032656232313935633537356136434d7576742f4946454b65687a704731765061534d786f4e4d6a55354d6a6b334f5441324f4473784d513d3d227d; JSESSIONID=5382A0486B551C57A731962A8AA2EFA9; l=dBxi3DBlQUuyHTSFBOfNIk0cjtQO1QAfCsPztJrHfICPOo5H5uDGWZVCIx8MCnGV3sevJ3uRJbTbB78iuyUIhxywiAxk-Ics6dTBR; isg=BFdXeEgZxeMjP0FrZCgX1-6f5suhnCv-TPhdrKmGHyau2HIasG-CTsG-OnhGMAN2'
    # refer = 'https://shopsearch.taobao.com/browse/shop_search.htm?q=%E5%90%96%E5%90%96%E5%AE%9D%E8%B4%9D&imgfile=&commend=all&ssid=s5-e&search_type=shop&sourceId=tb.index&spm=a21bo.2017.201856-taobao-item.1&ie=utf8&initiative_id=tbindexz_20170306'
    # refer='https://shopsearch.taobao.com/search/_____tmd_____/verify/?nc_token=a27aa55c9bee1be628ffec5b21c8adcf&nc_session_id=01-HjB-kYXOMkfuxTmpe8zA3nX89YkPI0vyu1HFfLaDavAg15-UvP-P0NMFQSKDhmTvGqPajwIxd4FjnNNe3irLfBR-EareDv78M979Y_GeBvXviFTnDRPANNk210c9DfX-sLAJKFB5UZI0rGQnTN_QQ&nc_sig=05VLrE9CrDc-AOy6tmwdVhkXbBS0XBA3ggGfp8lU3rfCVYj1nvP6LfQiQoVNq5YxW0HbzFFpUOFC-j-LCG0wU0SOPq1XTmN2ggJXJ8NMGQb0ZqxmNNoo42R70l2peP3-JZKKKJuUtI0ClrKeYtELOPPwPhT2pzPjz6mqkUJOU4NLLsFz1uDUgTGx2O_hRdsq9u08Z_BaLD2gLN4oOVzAN8dFfdKjgDfcNhYWoHGlQKhQDToy3Ukf-J_qrJbh4WrYkm4S3jrRidRqa_26JIhs5B_csBzUMsK165EDT6F8n9dyqpScAQtSRm4YGwOM5x6XbDtZ0rMbO718w2SYIHoW6_Id0ZEff-kAhHXAMbcadelUf92rGCa5x1aYIGUDcPazNZpmQvOFg1n_tYHxBng4JfqQ&x5secdata=5e0c8e1365474455070961b803bd560607b52cabf5960afff39b64ce58073f78286350d0cfa7f8fbea3fdf96851d2438c50f040819b04c592a744fe3c6fa5d65a88837e11b1f2fae4d3071fcede405c6056fdcb540117463ba325b185ae6e5611f7b11ffd5c77bcdd76cfb4200c2b549d7a69f689e1e3ba5f7c0f3bfdf92e4613a1ea640af08b3b5fdac0c6fc48c98139cbd445f4eb6be576477b81a8d9bfac2ebe5640d7fee42c0ef407b50395a47b292f87742993bd9dfea3647b745f1455c31d18ce548cb7abb31f72075b0394169c8a0079eef7fb4029525db2bba1628df50be1a3ab24ee57f866c2204ba502b292229ba3593585f1b7d03839620015ce5a68b0e67f838234417135b0cea4e94213b76d313ff08d9198c95dfd14d23a93fa3b3e7b92e7a104a939356775160b150c8f87dfe6e0d5a81928e8914e61ec20e697fc9f370c476feadb9eb87b0da835654ab43ab480ca6ffd3d310d4dd867f7aac62b8c07ac9734d6799e4f8b11e11a59dab80f89293688707c3aec5d53b80ed044651956336025df3602f748249715d46dc6973816d8cde281099d7bae4417e280b1481431fb26f2470faddfcdb18f1fa81ac484ce880b232aab3b48a625ccffb98f65805c85856c40ed5cded55ba0f49299593994d66b00986c474c00644211b295e6c1b520a1cb08bcfd7db44930bf40102fc3d07fa5ca982479aebf150f087ae44e200f5a44ed657a40ed30ec6e521b8d71b5018d3167fe6b955b8a3cc6913aa66354e36fd8e2409178f5a6306b27e35e29e895dd5559881ed86fa34fa7b&x5step=100&nc_app_key=X82Y__617ebfb52078a89d2b114c6cc750ce4a'
    # refer = 'https://shopsearch.taobao.com/search?q=%E6%A0%BC%E5%8A%9B&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20200217&ie=utf8&s=260'
    # cookie = 'thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; sgcookie=Q69w3TCSSIV1A0MXu7b6; uc3=nk2=ogVZTHsMoDEt1SMX&vt3=F8dBxdz0xkkgWiaszQ8%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UU27LTb4AXoiAA%3D%3D; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; uc4=nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvYJ9c%2BV9I8%3D&id4=0%40U2%2F8m%2FP6up3dR%2FWCyemFJJyG9IvL; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; _cc_=VT5L2FSpdA%3D%3D; tg=0; enc=0hS6oWCaJ8sQf63WozTa37bVyJjh1eSQuQ7taG5wphm97Es2PJo8gEQLDZtKKA2peIsvE1Ydg1Wp5%2FYXifgZdg%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; x5sec=7b2274616f62616f2d73686f707365617263683b32223a226466323433366634636239646534396233363939626466623466333535653830434a7a51742f4946454a2b56387537503936613274674561445449314f5449354e7a6b774e6a67374d54633d227d; JSESSIONID=679B7627205AF12D68DA4273B98AC0A2; isg=BIuL1zqYUR_vzo1PECQj-4LbGi91IJ-iULyRiP2ImkohHKl-j_UP8n369hzyPPea; l=cBxi3DBlQUuyHfVXBOfZhurza77O6IRbzsPzaNbMiICPOeCJ5fSCWZVCj0YvCnGVK6kwr3uRJbTbBJ8lryCq3Tt-CeE8Ggf..'
    # cookie = 'thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; sgcookie=Q69w3TCSSIV1A0MXu7b6; uc3=nk2=ogVZTHsMoDEt1SMX&vt3=F8dBxdz0xkkgWiaszQ8%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UU27LTb4AXoiAA%3D%3D; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; uc4=nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvYJ9c%2BV9I8%3D&id4=0%40U2%2F8m%2FP6up3dR%2FWCyemFJJyG9IvL; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; _cc_=VT5L2FSpdA%3D%3D; tg=0; enc=0hS6oWCaJ8sQf63WozTa37bVyJjh1eSQuQ7taG5wphm97Es2PJo8gEQLDZtKKA2peIsvE1Ydg1Wp5%2FYXifgZdg%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; x5sec=7b2274616f62616f2d73686f707365617263683b32223a2230663033636337346365316464646530323439653534633866333563646137634349367575664946454e71376862586c72706e5a6c774561445449314f5449354e7a6b774e6a67374d6a493d227d; JSESSIONID=EB8E736ED2E691E37F9D789AE66699FA; isg=BCcnCvkWNXAQNbH7FFhHZ16PtlvxrPuOHAiN3PmUQ7bd6EeqAXyL3mXqCuj2G9MG; l=cBxi3DBlQUuyHI2sBOCanurza77OSIRYYuPzaNbMi_5pA6T_cXbOoWki6F96VjWdtDYB44QKNE99-etkZym-rc8U-dWG.'
    # cookie = 'thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; sgcookie=Q69w3TCSSIV1A0MXu7b6; uc3=nk2=ogVZTHsMoDEt1SMX&vt3=F8dBxdz0xkkgWiaszQ8%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UU27LTb4AXoiAA%3D%3D; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; uc4=nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvYJ9c%2BV9I8%3D&id4=0%40U2%2F8m%2FP6up3dR%2FWCyemFJJyG9IvL; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; _cc_=VT5L2FSpdA%3D%3D; tg=0; enc=0hS6oWCaJ8sQf63WozTa37bVyJjh1eSQuQ7taG5wphm97Es2PJo8gEQLDZtKKA2peIsvE1Ydg1Wp5%2FYXifgZdg%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; JSESSIONID=9EC872A6ED6B6B7DAD7ABF65867B3A2D; x5sec=7b2274616f62616f2d73686f707365617263683b32223a223136663135613736323330353832353565643336343361376330623364613134434d433275664946454f72696e4b6e61674e663835514561445449314f5449354e7a6b774e6a67374d6a4d3d227d; isg=BIGB_Y1Zu57WfdetrhqZOcTtkM2brvWgVqprauPWJwjnyqCcK_oNca2LrD6MQo3Y; l=dBxi3DBlQUuyHjwiBOCNKk0cjtQTLIRfguPnnk2Bi_5L-6L_xr_OoWko0Fp6cjWcMcTB44QKNEwTrUZ8-ykZ0dttj3YHifMWBef..'
    # cookie = 'thw=cn; t=f5aa5a78ddbfd6ae06ab5359faecc239; cna=TejDFlyRknwCAd9aS81Wx6K4; _m_h5_tk=79f0ee9c8c294971d50fecfbff2191bb_1581916596866; _m_h5_tk_enc=02eb9bbcb381baa0bb3332eeaa4f7f20; lgc=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; tracknick=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; tg=0; hng=CN%7Czh-CN%7CCNY%7C156; mt=ci=44_1; _uab_collina=158191849753211586198949; enc=2gXK9wc2Cu353RNbOHaVOcLlHiGrk6uLaWvLBj%2FyRbUSLCe81yf%2FuBbAs8LgF3pxkl3b5jkXLiLQ4Vl0MXrckw%3D%3D; _samesite_flag_=true; cookie2=1c342ae1f8c8574ae882a987ac146c91; _tb_token_=e5e1b655eee0d; sgcookie=Du9wJwRI9MPgqvyGtFPE%2F; unb=2592979068; uc1=cookie14=UoTUOLFLcdNEtg%3D%3D&existShop=false&pas=0&lng=zh_CN&cookie21=Vq8l%2BKCLjhS4UhJVbhgU&tag=8&cookie16=VFC%2FuZ9az08KUQ56dCrZDlbNdA%3D%3D&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D; uc3=vt3=F8dBxdz4hhYlYxrF%2FBQ%3D&lg2=U%2BGCWk%2F75gdr5Q%3D%3D&nk2=ogVZTHsMoDEt1SMX&id2=UU27LTb4AXoiAA%3D%3D; csg=957dad49; cookie17=UU27LTb4AXoiAA%3D%3D; dnk=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; skt=e739ca8721cd50b5; existShop=MTU4MjI0NTkxNQ%3D%3D; uc4=id4=0%40U2%2F8m%2FP6up3dR%2FWCyemGBQwHisL2&nk4=0%40oAekTJ8TcKgdSvB1EK%2B8jvVQaR8%2FaJs%3D; _cc_=U%2BGCWk%2F7og%3D%3D; _l_g_=Ug%3D%3D; sg=%E5%90%AF8b; _nk_=%5Cu6D41%5Cu901D%5Cu5E74%5Cu534E%5Cu5BB6%5Cu542F; cookie1=BxJKhb3w1hP40MdadOqwYzyMQQ%2FBX0twFjoC3UKKX3U%3D; tfstk=cfNlB7Vua8k5XGee7QG7RlDFec1OZ3REjWPbg74qwfYoy4VVi_J2QCoPo0qu9p1..; JSESSIONID=00A5CA8EB5B3CD63F3091AE3E18B5167; isg=BFJSCXtzWKKeeqRYsYfadLMIoxg0Y1b9we-4_xyrfoXwL_IpBPOmDVjNm4sTRM6V; l=cBxi3DBlQUuyHhYSBOCanurza77OSIRYYuPzaNbMi_5HQ6T_PzbOoWqsDF96VjWdts8B44QKNE99-etuZLjox28U-dWG.'
    # cookie = 'hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; t=4ee589cbdf84f9c22e6028420193d8f1; cna=835WFiASHHUCAT2QIkpC45Bo; sgcookie=Q%2BAljdnUDf6VytEKA9Hj; uc3=id2=UNN9dgBrypr9hg%3D%3D&nk2=06uUNygXxr0%3D&lg2=UIHiLt3xD8xYTw%3D%3D&vt3=F8dBxdz3oVZwju5CR3g%3D; lgc=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; uc4=id4=0%40UgQ1KBe7v%2BBPdJ0t0h%2BG3ruYvaNS&nk4=0%400RBMkrnbwaCWx5BY3s1yaMyGXw%3D%3D; tracknick=%5Cu534A%5Cu6B87%5Cu304D%5Cu3042; _cc_=UtASsssmfA%3D%3D; tg=0; tfstk=b#BvNBH21AAHZFY61GTBVlfdiRwKOZLKMmJS5sQbPE+H0TMCGiVzAxcAlYi/+K1f==; mt=ci=6_1; v=0; cookie2=120f0d2623a721226b626a6cb9269fc8; _tb_token_=5e86163311313; enc=Z5UDQd9SOZD%2Bc0QwlkL3eFcZmQKH190UEUNfT63da4gEDVe6KrAgOt60tvsYzY40xue0HFNDz3Gkz57YGJmwPg%3D%3D; _samesite_flag_=true; uc1=cookie14=UoTUOLFLclHaLQ%3D%3D; JSESSIONID=892473EF95B252995990DAA252CA719A; isg=BFRUAKWR9khD-WGr4kBIP97zJZLGrXiXHxvQtO41xF9i2fYjF7h8J15f2dHBIbDv; l=cBQNSYhgq9IHPsFfBOCZourza779RIRVguPzaNbMi_5dK6863W_OoWqPPFJ6cjWht5Tp4dH2-seT3Ub4JIkVF3H6JuFfq'
    # refer = 'https://shopsearch.taobao.com/search?ie=utf8&initiative_id=staobaoz_20200221&js=1&q=%E5%A5%88%E7%B1%B3%E7%88%B1&suggest=0_2&_input_charset=utf-8&wq=%E5%A5%88%E7%B1%B3&suggest_query=%E5%A5%88%E7%B1%B3&source=suggest'
    # import redis
    # flag = False
    # redisdb = redis.Redis(host='127.0.0.1', port=6379)
    # while True:
    #
    #     res = redisdb.spop("taobao")
    #     print(res.decode("utf8"))
    #     if not res:
    #         print("品牌遍历完成")
    #         break
    #     # wd = input("输入品牌：")
    #     if flag:
    #         print("请更换cookie")
    #         cookie = input("cookie:")
    #         t_b = TaoBao(cookie,refer, res)
    #         t_b.run()
    #         flag = False
    #     else:
    #         t_b = TaoBao(cookie, refer, res)
    #         t_b.run()
    #     time.sleep(3.0)

# https://shopsearch.taobao.com/search?data-key=s&data-value=120&ajax=true&_ksTS=1582263895573_894&callback=jsonp895&q=%E5%87%89%E9%9E%8B&js=1&initiative_id=staobaoz_20200221&ie=utf8&s=100
