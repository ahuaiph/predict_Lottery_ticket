import time
import random
import requests
import base64
import argparse
import shutil
import os
from get_data import get_run
from run_predict import maini
from run_train_model import train_run

parser = argparse.ArgumentParser()
parser.add_argument('--type', default="ssq", type=str, help="选择训练数据: ssq/dlt")
parser.add_argument('--name', default="双色球", type=str, help="请输入彩票类型: 双色球/大乐透")
args = parser.parse_args()


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
    title = '彩票预测结果通知!'
    content = msg
    template = 'html'
    url = f"https://www.pushplus.plus/send?token={token}&title={title}&content={content}&template={template}"
    print('%s 正在通过pushplus发送消息到微信，请注意查收！' % now_times())
    requests.get(url=url)
    print('%s pushplus消息发送成功，请登录微信进行查收！' % now_times())

def folder():
    path = os.getcwd()
    path1 = path + '\data'
    path2 = path + '\model'
    t1 = os.path.exists(path1)
    t2 = os.path.exists(path2)
    if t1:
        shutil.rmtree(path1)
        print('文件夹：' + path1 + '删除成功')
    elif t2:
        shutil.rmtree(path2)
        print('文件夹：' + path2 + '删除成功')

def main():
    folder()
    type = args.type
    name = args.name
    get_run(name=type)
    print(f'{now_times()} 正在获取大乐透数据！')
    train_run(name=type)
    print(f'{now_times()} 正在训练大乐透数据模型！')
    result_code = maini(name=type)
    print(f'{now_times()} 正在获取大乐透预测！')
    send_wechat(f'{now_times()} {name} {result_code}，预测结果已经发送！请及时查看！')

if __name__ == '__main__':
    main()