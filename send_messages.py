import time
import random
import requests
import base64
import os
from get_data import get_run
# from run_predict import predict_run
# from run_train_model import train_run


def time_sleep(a, b):
    k = random.randint(a, b)
    print('%s 正在休眠%ss...' % (now_times(), k))
    time.sleep(k)
    return k


def now_times():
    cc = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return cc


def send_wechat(msg):
    token = 'b05888bee9e54c399927600ecb3e8ae5'
    title = '小米13定制版有消息!'
    content = msg
    template = 'html'
    url = f"https://www.pushplus.plus/send?token={token}&title={title}&content={content}&template={template}"
    print('%s 正在通过pushplus发送消息到微信，请注意查收！' % now_times())
    requests.get(url=url)
    print('%s pushplus消息发送成功，请登录微信进行查收！' % now_times())
    time_sleep(4, 8)



if __name__ == '__main__':
    type = 'dlt'
    get_run(name=type)
    print(f'{now_times()} 正在获取大乐透数据！')
    # train_run(name=type)
    # print(f'{now_times()} 正在训练大乐透数据模型！')
    # predict_run(name=type)
    # print(f'{now_times()} 正在获取大乐透预测！')
    # send_wechat(f'{now_times()} />')