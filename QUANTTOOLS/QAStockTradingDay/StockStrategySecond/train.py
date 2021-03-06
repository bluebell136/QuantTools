#coding=utf-8

from QUANTTOOLS.QAStockTradingDay.StockStrategyFirst.setting import working_dir
from QUANTTOOLS.QAStockTradingDay.StockModel.StrategyOne import model as StockModel
from QUANTTOOLS.QAIndexTradingDay.IndexModel.IndexStrategyOne import model as IndexModel
from QUANTTOOLS.message_func import build_head, build_table, build_email, send_email
import pandas as pd
from QUANTAXIS.QAUtil import (QA_util_log_info)
from QUANTTOOLS.message_func.wechat import send_actionnotice
from datetime import datetime,timedelta
delta = timedelta(days=6)
delta1 = timedelta(days=1)
delta3 = timedelta(days=7)
delta4 = timedelta(days=8)

def train(date, strategy_id='机器学习1号', working_dir=working_dir, ui_log = None):
    QA_util_log_info(
        '##JOB01 Now Model Init ==== {}'.format(str(date)), ui_log)
    stock_model = StockModel()
    index_model = IndexModel()
    QA_util_log_info(
        '##JOB02 Now Prepare Date ==== {}'.format(str(date)), ui_log)
    stock_model.get_data(start=str(int(date[0:4])-3)+"-01-01", end=date)
    QA_util_log_info(
        '##JOB03 Now Set Target ==== {}'.format(str(date)), ui_log)
    stock_model.set_target(mark =0.42, type = 'percent')
    QA_util_log_info(
        '##JOB04 Now Set Train time range ==== {}'.format(str(date)), ui_log)
    stock_model.set_train_rng(train_start=str(int(date[0:4])-3)+"-01-01",
                        train_end=(datetime.strptime(date, "%Y-%m-%d")-delta4).strftime('%Y-%m-%d'),
                        test_start=(datetime.strptime(date, "%Y-%m-%d")-delta3).strftime('%Y-%m-%d'),
                        test_end=date)
    stock_model.prepare_data()
    stock_model.build_model(n_estimators=200)
    QA_util_log_info(
        '##JOB05 Now Model Trainnig ==== {}'.format(str(date)), ui_log)
    stock_model.model_running()
    stock_model.model_check()
    QA_util_log_info(
        '##JOB06 Now Save Model ==== {}'.format(str(date)), ui_log)
    important = stock_model.model_important()
    stock_model.save_model('stock',working_dir = working_dir)
    body1 = build_table(pd.DataFrame(stock_model.info['train_report']), '个股模型训练集情况')
    body2 = build_table(pd.DataFrame(stock_model.info['test_report']), '个股模型测试集情况')
    body3 = build_table(important.head(50), '个股模型特征重要性')

    msg1 = '模型训练日期:{model_date}'.format(model_date=stock_model.info['date'])
    del stock_model

    QA_util_log_info(
        '##JOB02 Now Prepare Date ==== {}'.format(str(date)), ui_log)
    index_model.get_data(start=str(int(date[0:4])-3)+"-01-01", end=date)
    QA_util_log_info(
        '##JOB03 Now Set Target ==== {}'.format(str(date)), ui_log)
    index_model.set_target('INDEX_TARGET5', mark = 0.3, type = 'percent')
    QA_util_log_info(
        '##JOB04 Now Set Train time range ==== {}'.format(str(date)), ui_log)
    index_model.set_train_rng(train_start=str(int(date[0:4])-3)+"-01-01",
                              train_end=(datetime.strptime(date, "%Y-%m-%d")-delta4).strftime('%Y-%m-%d'),
                              test_start=(datetime.strptime(date, "%Y-%m-%d")-delta3).strftime('%Y-%m-%d'),
                              test_end=date)
    index_model.prepare_data()
    index_model.build_model(n_estimators=200)
    QA_util_log_info(
        '##JOB05 Now Model Trainnig ==== {}'.format(str(date)), ui_log)
    index_model.model_running()
    index_model.model_check()
    QA_util_log_info(
        '##JOB06 Now Save Model ==== {}'.format(str(date)), ui_log)
    important = index_model.model_important()
    index_model.save_model('index',working_dir = working_dir)
    body4 = build_table(pd.DataFrame(index_model.info['train_report']), '指数模型训练集情况')
    body5 = build_table(pd.DataFrame(index_model.info['test_report']), '指数模型测试集情况')
    body6 = build_table(important.head(50), '指数模型特征重要性')

    index_model.set_target('INDEX_TARGET', mark = 0.3, type = 'percent')
    index_model.prepare_data()
    index_model.build_model(n_estimators=200)
    index_model.model_running()
    index_model.model_check()
    index_model.save_model('safe',working_dir = working_dir)

    body7 = build_table(pd.DataFrame(index_model.info['train_report']), '安全模型训练集情况')
    body8 = build_table(pd.DataFrame(index_model.info['test_report']), '安全模型测试集情况')
    body9 = build_table(important.head(50), '安全模型特征重要性')

    QA_util_log_info(
        '##JOB06 Now Model Trainning Report ==== {}'.format(str(date)), ui_log)
    msg = build_email(build_head(),msg1,body1,body2,body3,body4,body5,body6,body7,body8,body9)

    send_email('模型训练报告', msg, 'date')
    send_actionnotice(strategy_id,
                      '报告:{}'.format(date),
                      '模型训练完成,请查收结果',
                      direction = 'HOLD',
                      offset='HOLD',
                      volume=None
                      )