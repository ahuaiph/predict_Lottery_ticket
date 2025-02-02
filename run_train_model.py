# -*- coding:utf-8 -*-
"""
Author: BigCat
"""
import time
import json
import argparse
import numpy as np
import pandas as pd
from config import *
from modeling import LstmWithCRFModel, SignalLstmModel, tf
from loguru import logger

# parser = argparse.ArgumentParser()
# parser.add_argument('--name', default="ssq", type=str, help="选择训练数据: 双色球/大乐透")
# args = parser.parse_args()

pred_key = {}


def create_train_data(name, windows):
    """ 创建训练数据
    :param name: 玩法，双色球/大乐透
    :param windows: 训练窗口
    :return:
    """
    data = pd.read_csv("{}{}".format(name_path[name]["path"], data_file_name))
    if not len(data):
        raise logger.error(" 请执行 get_data.py 进行数据下载！")
    else:
        # 创建模型文件夹
        if not os.path.exists(model_path):
            os.mkdir(model_path)
        logger.info("训练数据已加载! ")

    data = data.iloc[:, 2:].values
    logger.info("训练集数据维度: {}".format(data.shape))
    x_data, y_data = [], []
    for i in range(len(data) - windows - 1):
        sub_data = data[i:(i+windows+1), :]
        x_data.append(sub_data[1:])
        y_data.append(sub_data[0])

    cut_num = 6 if name == "ssq" else 5
    return {
        "red": {
            "x_data": np.array(x_data)[:, :, :cut_num], "y_data": np.array(y_data)[:, :cut_num]
        },
        "blue": {
            "x_data": np.array(x_data)[:, :, cut_num:], "y_data": np.array(y_data)[:, cut_num:]
        }
    }


def train_red_ball_model(name, x_data, y_data):
    """ 红球模型训练
    :param name: 玩法
    :param x_data: 训练样本
    :param y_data: 训练标签
    :return:
    """
    m_args = model_args[name]
    x_data = x_data - 1
    y_data = y_data - 1
    data_len = x_data.shape[0]
    logger.info("特征数据维度: {}".format(x_data.shape))
    logger.info("标签数据维度: {}".format(y_data.shape))
    with tf.compat.v1.Session() as sess:
        red_ball_model = LstmWithCRFModel(
            batch_size=m_args["model_args"]["batch_size"],
            n_class=m_args["model_args"]["red_n_class"],
            ball_num=m_args["model_args"]["sequence_len"] if name == "ssq" else m_args["model_args"]["red_sequence_len"],
            w_size=m_args["model_args"]["windows_size"],
            embedding_size=m_args["model_args"]["red_embedding_size"],
            words_size=m_args["model_args"]["red_n_class"],
            hidden_size=m_args["model_args"]["red_hidden_size"],
            layer_size=m_args["model_args"]["red_layer_size"]
        )
        train_step = tf.compat.v1.train.AdamOptimizer(
            learning_rate=m_args["train_args"]["red_learning_rate"],
            beta1=m_args["train_args"]["red_beta1"],
            beta2=m_args["train_args"]["red_beta2"],
            epsilon=m_args["train_args"]["red_epsilon"],
            use_locking=False,
            name='Adam'
        ).minimize(red_ball_model.loss)
        sess.run(tf.compat.v1.global_variables_initializer())
        for epoch in range(m_args["model_args"]["red_epochs"]):
            for i in range(data_len):
                _, loss_, pred = sess.run([
                    train_step, red_ball_model.loss, red_ball_model.pred_sequence
                ], feed_dict={
                    "inputs:0": x_data[i:(i+1), :, :],
                    "tag_indices:0": y_data[i:(i+1), :],
                    "sequence_length:0": np.array([m_args["model_args"]["sequence_len"]]*1) \
                        if name == "ssq" else np.array([m_args["model_args"]["red_sequence_len"]]*1)
                })
                if i % 100 == 0:
                    logger.info("epoch: {}, loss: {}, tag: {}, pred: {}".format(
                        epoch, loss_, y_data[i:(i+1), :][0] + 1, pred[0] + 1)
                    )
        pred_key[ball_name[0][0]] = red_ball_model.pred_sequence.name
        if not os.path.exists(m_args["path"]["red"]):
            os.makedirs(m_args["path"]["red"])
        saver = tf.compat.v1.train.Saver()
        saver.save(sess, "{}{}.{}".format(m_args["path"]["red"], red_ball_model_name, extension))


def train_blue_ball_model(name, x_data, y_data):
    """ 蓝球模型训练
    :param name: 玩法
    :param x_data: 训练样本
    :param y_data: 训练标签
    :return:
    """
    m_args = model_args[name]
    x_data = x_data - 1
    data_len = x_data.shape[0]
    if name == "ssq":
        x_data = x_data.reshape(len(x_data), m_args["model_args"]["windows_size"])
        y_data = tf.keras.utils.to_categorical(y_data - 1, num_classes=m_args["model_args"]["blue_n_class"])
    logger.info("特征数据维度: {}".format(x_data.shape))
    logger.info("标签数据维度: {}".format(y_data.shape))
    with tf.compat.v1.Session() as sess:
        if name == "ssq":
            blue_ball_model = SignalLstmModel(
                batch_size=m_args["model_args"]["batch_size"],
                n_class=m_args["model_args"]["blue_n_class"],
                w_size=m_args["model_args"]["windows_size"],
                embedding_size=m_args["model_args"]["blue_embedding_size"],
                hidden_size=m_args["model_args"]["blue_hidden_size"],
                outputs_size=m_args["model_args"]["blue_n_class"],
                layer_size=m_args["model_args"]["blue_layer_size"]
            )
        else:
            blue_ball_model = LstmWithCRFModel(
                batch_size=m_args["model_args"]["batch_size"],
                n_class=m_args["model_args"]["blue_n_class"],
                ball_num=m_args["model_args"]["blue_sequence_len"],
                w_size=m_args["model_args"]["windows_size"],
                embedding_size=m_args["model_args"]["blue_embedding_size"],
                words_size=m_args["model_args"]["blue_n_class"],
                hidden_size=m_args["model_args"]["blue_hidden_size"],
                layer_size=m_args["model_args"]["blue_layer_size"]
            )
        train_step = tf.compat.v1.train.AdamOptimizer(
            learning_rate=m_args["train_args"]["blue_learning_rate"],
            beta1=m_args["train_args"]["blue_beta1"],
            beta2=m_args["train_args"]["blue_beta2"],
            epsilon=m_args["train_args"]["blue_epsilon"],
            use_locking=False,
            name='Adam'
        ).minimize(blue_ball_model.loss)
        sess.run(tf.compat.v1.global_variables_initializer())
        for epoch in range(m_args["model_args"]["blue_epochs"]):
            for i in range(data_len):
                if name == "ssq":
                    _, loss_, pred = sess.run([
                        train_step, blue_ball_model.loss, blue_ball_model.pred_label
                    ], feed_dict={
                        "inputs:0": x_data[i:(i+1), :],
                        "tag_indices:0": y_data[i:(i+1), :],
                    })
                    if i % 100 == 0:
                        logger.info("epoch: {}, loss: {}, tag: {}, pred: {}".format(
                            epoch, loss_, np.argmax(y_data[i:(i+1), :][0]) + 1, pred[0] + 1)
                        )
                else:
                    _, loss_, pred = sess.run([
                        train_step, blue_ball_model.loss, blue_ball_model.pred_sequence
                    ], feed_dict={
                        "inputs:0": x_data[i:(i + 1), :, :],
                        "tag_indices:0": y_data[i:(i + 1), :],
                        "sequence_length:0": np.array([m_args["model_args"]["blue_sequence_len"]] * 1)
                    })
                    if i % 100 == 0:
                        logger.info("epoch: {}, loss: {}, tag: {}, pred: {}".format(
                            epoch, loss_, y_data[i:(i + 1), :][0] + 1, pred[0] + 1)
                        )
        pred_key[ball_name[1][0]] = blue_ball_model.pred_label.name if name == "ssq" else blue_ball_model.pred_sequence.name
        if not os.path.exists(m_args["path"]["blue"]):
            os.mkdir(m_args["path"]["blue"])
        saver = tf.compat.v1.train.Saver()
        saver.save(sess, "{}{}.{}".format(m_args["path"]["blue"], blue_ball_model_name, extension))


def train_run(name):
    """ 执行训练
    :param name: 玩法
    :return:
    """

    logger.info("正在创建【{}】数据集...".format(name_path[name]["name"]))
    # train_data = create_train_data(args.name, model_args[name]["model_args"]["windows_size"])
    train_data = create_train_data(name, model_args[name]["model_args"]["windows_size"])

    logger.info("开始训练【{}】红球模型...".format(name_path[name]["name"]))
    start_time = time.time()
    train_red_ball_model(name, x_data=train_data["red"]["x_data"], y_data=train_data["red"]["y_data"])
    logger.info("训练耗时: {}".format(time.time() - start_time))

    tf.compat.v1.reset_default_graph()  # 重置网络图

    logger.info("开始训练【{}】蓝球模型...".format(name_path[name]["name"]))
    start_time = time.time()
    train_blue_ball_model(name, x_data=train_data["blue"]["x_data"], y_data=train_data["blue"]["y_data"])
    logger.info("训练耗时: {}".format(time.time() - start_time))

    # 保存预测关键结点名
    with open("{}/{}/{}".format(model_path, name, pred_key_name), "w") as f:
        json.dump(pred_key, f)


if __name__ == '__main__':
    # if not args.name:
    #     raise Exception("玩法名称不能为空！")
    # else:
    #     train_run(args.name)
    train_run('dlt')
