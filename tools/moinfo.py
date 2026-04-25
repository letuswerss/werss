# -*- coding: UTF-8 -*-
import time

import requests
import pandas as pd


def getMoreInfo(link):
    # 获得mid,_biz,idx,sn 这几个在link中的信息
    mid = link.split("&")[1].split("=")[1]
    idx = link.split("&")[2].split("=")[1]
    sn = link.split("&")[3].split("=")[1]
    _biz = link.split("&")[0].split("_biz=")[1]

    # fillder 中取得一些不变得信息
    # req_id = "0614ymV0y86FlTVXB02AXd8p"
    pass_ticket = ""  # 从fiddler中获取
    appmsg_token = ""  # 从fiddler中获取
    uin = "" # 从fiddler 中获取
    key = "" # 从fiddler 中获取

    # 目标url
    url = "http://mp.weixin.qq.com/mp/getappmsgext"  # 获取详情页的网址
    # 添加Cookie避免登陆操作，这里的"User-Agent"最好为手机浏览器的标识
    phoneCookie = "" # 从fiddler 中获取 
    headers = {
        "Cookie": phoneCookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63070517)"
    }
    # 添加data，`req_id`、`pass_ticket`分别对应文章的信息，从fiddler复制即可。
    data = {
        "is_only_read": "1",
        "is_temp_url": "0",
        "appmsg_type": "9",
        'reward_uin_count': '0'
    }
    """
    添加请求参数
    __biz对应公众号的信息，唯一
    mid、sn、idx分别对应每篇文章的url的信息，需要从url中进行提取
    key、appmsg_token从fiddler上复制即可
    pass_ticket对应的文章的信息，也可以直接从fiddler复制
    """
    params = {
        "__biz": _biz,
        "mid": mid,
        "sn": sn,
        "idx": idx,
        "key": key,
        "pass_ticket": pass_ticket,
        "appmsg_token": appmsg_token,
        "uin": uin,
        "wxtoken": "777",
    }

    content = requests.post(url, headers=headers, data=data, params=params).json()
    # 提取其中的阅读数和点赞数
    print(content["appmsgstat"]["read_num"], content["appmsgstat"]["like_num"])
    try:
        readNum = content["appmsgstat"]["read_num"]
        print("阅读数:" + str(readNum))
    except:
        readNum = 0
    try:
        likeNum = content["appmsgstat"]["like_num"]
        print("喜爱数:" + str(likeNum))
    except:
        likeNum = 0
    try:
        old_like_num = content["appmsgstat"]["old_like_num"]
        print("在读数:" + str(old_like_num))
    except:
        old_like_num = 0

    return readNum, likeNum, old_like_num



df = pd.read_csv("data.csv")
try:
    for index, row in enumerate(df.itertuples()):
        readNum, likeNum, old_like_num = getMoreInfo(row.url)
        df.loc[index, 'likeNum'] = likeNum
        df.loc[index, 'readNum'] = readNum
        df.loc[index, 'old_like_num'] = old_like_num
        print(row.url)
        # 歇3s，防止被封
        time.sleep(3)
except Exception as e:
    print(e)
df.to_csv("data1.csv")