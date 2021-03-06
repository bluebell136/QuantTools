from QUANTAXIS.QAFetch.QAQuery import QA_fetch_stock_list
from QUANTAXIS.QAFetch import QA_fetch_get_stock_realtime
from QUANTTOOLS.message_func.wechat import send_actionnotice
from QUANTTOOLS.QAStockETL.QAFetch import QA_fetch_stock_fianacial_adv
from QUANTAXIS.QAFetch.QAQuery_Advance import QA_fetch_stock_day_adv
import pandas as pd
import logging
import strategyease_sdk
from QUANTTOOLS.account_manage.setting import yun_ip, yun_port, easytrade_password
import time
import datetime
from QUANTTOOLS.account_manage.trading_message import send_trading_message
from QUANTAXIS.QAUtil import QA_util_get_last_day
from QUANTAXIS.QAFetch.QAQuery import QA_fetch_stock_to_market_date
from QUANTAXIS.QAUtil import QA_util_today_str
import math

def date_func(date):
    if (date is None) or date in ['None', 0, '0']:
        d2 = datetime.datetime.strptime(QA_util_today_str(),"%Y-%m-%d")
    else:
        d2=datetime.datetime.strptime(date,"%Y%m%d")
    d1 = datetime.datetime.strptime(QA_util_today_str(),"%Y-%m-%d")
    diff_days=d1-d2
    return(diff_days.days)

def func1(x,y):
    if x == 0:
        return y
    else:
        return x

def re_build(target, positions, sub_accounts, trading_date, percent, exceptions, k=100):
    sub_accounts= sub_accounts -10000
    positions = positions[positions['股票余额'].astype(float) > 0]
    positions = positions[positions['股票余额'].astype(float) > 0]
    positions['上市时间'] = positions['证券代码'].apply(lambda x:date_func(str(QA_fetch_stock_to_market_date(x))))

    if exceptions is not None:
        exceptions = exceptions.extend(list(positions[positions['上市时间'] <= 15].set_index('证券代码').index))
    else:
        exceptions = list(positions[positions['上市时间'] <= 15].set_index('证券代码').index)

    if target is None:
        res = pd.concat([positions.set_index('证券代码'),
                         QA_fetch_stock_fianacial_adv(list(positions.set_index('证券代码').index), trading_date, trading_date).data.reset_index('date')[['NAME','INDUSTRY']],
                         QA_fetch_stock_day_adv(list(positions.set_index('证券代码').index),QA_util_get_last_day(trading_date,60),trading_date).to_qfq().data.loc[trading_date].reset_index('date')['close']],
                        axis=1)
        if exceptions is not None:
            exceptions_list = [i for i in list(res.index) if i not in exceptions]
            res = res.loc[exceptions_list]
        else:
            pass
        avg_account = 0
        res = res.assign(tar=avg_account)
        res['cnt'] = 0
        res['real'] = 0
        res['mark'] = (res['cnt'] - res['股票余额'].apply(lambda x:float(x))).apply(lambda x:math.floor(x/100)*100)
    else:
        tar1 = target.reset_index().groupby('code').max()
        tar1['double'] = target.reset_index().groupby('code')['RANK'].count()
        target = tar1
        if exceptions is not None:
            exceptions_list = [i for i in list(target.index) if i not in exceptions]
            exceptions_listb = [i for i in list(positions.set_index('证券代码').index) if i not in exceptions]
            r1 = target.loc[exceptions_list].join(positions.set_index('证券代码').loc[exceptions_listb],how='outer')
        else:
            r1 = target.join(positions.set_index('证券代码'),how='outer')
        r1['股票余额'] = r1['股票余额'].fillna(0)
        realtm = QA_fetch_get_stock_realtime('tdx', code=[x for x in list(r1.index) if x in list(QA_fetch_stock_list().index)]).reset_index('datetime')[['ask1','ask_vol1','bid1','bid_vol1']]
        close = QA_fetch_stock_day_adv(list(r1.index),QA_util_get_last_day(trading_date,60),trading_date).data.loc[trading_date].reset_index('date')['close']
        res = r1.join(QA_fetch_stock_fianacial_adv(list(r1.index), trading_date, trading_date).data.reset_index('date')[['NAME','INDUSTRY']],how='left').join(realtm,how='left').join(close,how='left')
        avg_account = (sub_accounts * percent)/target['double'].sum()
        res = res.assign(tar=avg_account)
        res.ix[res['RANK'].isnull(),'tar'] = 0
        res['tar'] = res['tar'] * res['double']
        res['amt'] = res.apply(lambda x: func1(x['ask1'], x['bid1']),axis = 1)
        res['cnt'] = (res['tar']/res['amt']/100).apply(lambda x: round(x, 0)*100)
        res['real'] = res['cnt'] * res['amt']
        res = res.sort_values(by='amt', ascending= False)
        res = res.fillna(0)
        res1 = res[res['tar']>0]
        res2 = res[res['tar']==0]
        res1.ix[-1, 'cnt'] = round((res1['real'][-1]-(res1['real'].sum()-res1['tar'].sum()))/res1['ask1'][-1]/100,0)*100-k
        res = pd.concat([res1,res2])
        res['real'] = res['cnt'] * res['amt']
        res['mark'] = (res['cnt'] - res['股票余额'].apply(lambda x:float(x))).apply(lambda x:math.floor(x/100)*100)
    return(res)

def build(target, positions, sub_accounts, trading_date, percent, exceptions, k=100):
    res = re_build(target, positions, sub_accounts, trading_date, percent, exceptions,k=k)
    while res['tar'].sum() < res['real'].sum():
        k = k+100
        res = re_build(target, positions, sub_accounts, trading_date, percent, exceptions,k=k)
    return(res)

def trade_roboot(target, account, trading_date,percent, strategy_id, type='end', exceptions = None):
    logging.basicConfig(level=logging.DEBUG)
    client = strategyease_sdk.Client(host=yun_ip, port=yun_port, key=easytrade_password)
    account1=account
    client.cancel_all(account1)
    account_info = client.get_account(account1)
    sub_accounts = client.get_positions(account1)['sub_accounts']['总 资 产'].values[0]
    try:
        frozen = float(client.get_positions(account1)['positions'].set_index('证券代码').loc[exceptions]['市值'].sum())
    except:
        frozen = 0
    sub_accounts = sub_accounts - frozen
    positions = client.get_positions(account1)['positions'][['证券代码','证券名称','股票余额','可用余额','冻结数量','参考盈亏','盈亏比例(%)']]

    if target is None:
        e = send_trading_message(account1, strategy_id, account_info, None, "触发清仓", None, 0, direction = 'SELL', type='MARKET', priceType=4,price=None, client=client)

    res = build(target, positions, sub_accounts, trading_date, percent, exceptions,100)
    res1 = res

    while (res[res['mark']<0].shape[0] + res[res['mark']>0].shape[0]) > 0:

        h1 = int(datetime.datetime.now().strftime("%H"))
        if h1 >= 15 :
            break

        if res[res['mark']<0].shape[0] == 0:
            pass
        else:
            for i in res[res['mark'] < 0].index:
                if type == 'end':
                    cnt = float(res.at[i, 'cnt'])
                    tar = float(res.at[i, '股票余额'])
                    NAME = res.at[i, 'NAME']
                    INDUSTRY = res.at[i, 'INDUSTRY']
                    mark = abs(float(res.at[i, 'mark']))

                    print('卖出 {code}({NAME},{INDUSTRY}) {cnt}股, 目标持仓:{target},总金额:{tar}'.format(code=i,
                                                                                                NAME= NAME,
                                                                                                INDUSTRY= INDUSTRY,
                                                                                                cnt=abs(mark),
                                                                                                target=cnt,
                                                                                                tar=tar))
                    e = send_trading_message(account1, strategy_id, account_info, i, NAME, INDUSTRY, mark, direction = 'SELL', type='MARKET', priceType=4, price=None, client=client)
                elif type == 'morning':
                    cnt = float(res.at[i, 'cnt'])
                    tar = float(res.at[i, '股票余额'])
                    NAME = res.at[i, 'NAME']
                    INDUSTRY = res.at[i, 'INDUSTRY']
                    mark = abs(float(res.at[i, 'mark']))
                    price = round(float(res.at[i, 'close']*1.0995),2)
                    print('早盘挂单卖出 {code}({NAME},{INDUSTRY}) {cnt}股, 目标持仓:{target},单价:{price},总金额:{tar}'.format(code=i,
                                                                                                NAME= NAME,
                                                                                                INDUSTRY= INDUSTRY,
                                                                                                cnt=abs(mark),
                                                                                                target=cnt,
                                                                                                tar=tar,
                                                                                                price=price))
                    e = send_trading_message(account1, strategy_id, account_info, i, NAME, INDUSTRY, mark, direction = 'SELL', type='LIMIT', priceType=None, price=price, client=client)
                else:
                    pass
                time.sleep(5)

        time.sleep(30)

        for i in res[res['mark'] == 0].index:
            cnt = float(res.at[i, 'cnt'])
            tar = float(res.at[i, 'real'])
            NAME = res.at[i, 'NAME']
            INDUSTRY = res.at[i, 'INDUSTRY']
            mark = abs(float(res.at[i, 'mark']))
            print('继续持有 {code}({NAME},{INDUSTRY}), 目标持仓:{target},总金额:{tar}'.format(code=i,
                                                                                   NAME= NAME,
                                                                                   INDUSTRY=INDUSTRY,
                                                                                   target=cnt,
                                                                                   tar=tar))
            send_actionnotice(strategy_id,
                              account_info,
                              '{code}({NAME},{INDUSTRY})'.format(code=i,NAME= NAME, INDUSTRY=INDUSTRY),
                              direction = 'HOLD',
                              offset='HOLD',
                              volume=abs(mark)
                              )
        time.sleep(10)

        if res[res['mark'] > 0].shape[0] == 0:
            pass
        else:
            for i in res[res['mark'] > 0].index:
                if type == 'end':
                    cnt = float(res.at[i, 'cnt'])
                    tar = float(res.at[i, 'real'])
                    NAME = res.at[i, 'NAME']
                    INDUSTRY = res.at[i, 'INDUSTRY']
                    mark = abs(float(res.at[i, 'mark']))
                    print('买入 {code}({NAME},{INDUSTRY}) {cnt}股, 目标持仓:{target},总金额:{tar}'.format(code=i,
                                                                                                NAME= NAME,
                                                                                                INDUSTRY=INDUSTRY,
                                                                                                cnt=abs(mark),
                                                                                                target=cnt,
                                                                                                tar=tar))
                    e = send_trading_message(account1, strategy_id, account_info, i, NAME, INDUSTRY, mark, direction = 'BUY', type='MARKET', priceType=4, price = None, client=client)
                elif type == 'morning':
                    cnt = float(res.at[i, 'cnt'])
                    tar = float(res.at[i, 'real'])
                    NAME = res.at[i, 'NAME']
                    INDUSTRY = res.at[i, 'INDUSTRY']
                    mark = abs(float(res.at[i, 'mark']))
                    price = round(float(res.at[i, 'close']*(1-0.0995)),2)
                    print('早盘挂单买入 {code}({NAME},{INDUSTRY}) {cnt}股, 目标持仓:{target},单价:{price},总金额:{tar}'.format(code=i,
                                                                                                NAME= NAME,
                                                                                                INDUSTRY=INDUSTRY,
                                                                                                cnt=abs(mark),
                                                                                                target=cnt,
                                                                                                price=price,
                                                                                                tar=tar))
                    e = send_trading_message(account1, strategy_id, account_info, i, NAME, INDUSTRY, mark, direction = 'BUY', type='LIMIT', priceType=None, price=price, client=client)
                else:
                    pass
                time.sleep(5)

        time.sleep(30)
        if type == 'end':
            sub_accounts = client.get_positions(account1)['sub_accounts']['总 资 产'].values[0] - frozen
            positions = client.get_positions(account1)['positions'][['证券代码','证券名称','股票余额','可用余额','冻结数量','参考盈亏','盈亏比例(%)']]
            res = build(target, positions, sub_accounts, trading_date, percent, exceptions,100)
        elif type == 'morning':
            break
        else:
            break

    return(res1)