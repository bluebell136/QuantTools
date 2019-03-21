
import numpy
import pandas as pd

from QUANTAXIS.QAUtil import (DATABASE, QA_util_date_stamp,
                              QA_util_date_valid, QA_util_log_info, QA_util_code_tolist, QA_util_date_str2int, QA_util_date_int2str,
                              QA_util_to_json_from_pandas)
from QUANTTOOLS.QAStockETL.FuncTools.financial_mean import financial_dict

def QA_fetch_financial_report(code, report_date, type ='report', ltype='EN', db=DATABASE):
    """获取专业财务报表

    Arguments:
        code {[type]} -- [description]
        report_date {[type]} -- [description]

    Keyword Arguments:
        ltype {str} -- [description] (default: {'EN'})
        db {[type]} -- [description] (default: {DATABASE})

    Raises:
        e -- [description]

    Returns:
        pd.DataFrame -- [description]
    """

    if isinstance(code, str):
        code = [code]
    if isinstance(report_date, str):
        report_date = [QA_util_date_str2int(report_date)]
    elif isinstance(report_date, int):
        report_date = [report_date]
    elif isinstance(report_date, list):
        report_date = [QA_util_date_str2int(item) for item in report_date]

    collection = db.financial
    num_columns = [item[:3] for item in list(financial_dict.keys())]
    CH_columns = [item[3:] for item in list(financial_dict.keys())]
    EN_columns = list(financial_dict.values())
    #num_columns.extend(['283', '_id', 'code', 'report_date'])
    # CH_columns.extend(['283', '_id', 'code', 'report_date'])
    #CH_columns = pd.Index(CH_columns)
    #EN_columns = list(financial_dict.values())
    #EN_columns.extend(['283', '_id', 'code', 'report_date'])
    #EN_columns = pd.Index(EN_columns)


    try:
        if type == 'report':
            if code is not None and report_date is not None:
                data = [item for item in collection.find(
                    {'code': {'$in': code}, 'report_date': {'$in': report_date}}, batch_size=10000)]
            elif code is None and report_date is not None:
                data = [item for item in collection.find(
                    {'report_date': {'$in': report_date}}, batch_size=10000)]
            elif code is not None and report_date is None:
                data = [item for item in collection.find(
                    {'code': {'$in': code}}, batch_size=10000)]
            else:
                data = [item for item in collection.find()]

        elif type == 'date':
            if code is not None and report_date is not None:
                data = [item for item in collection.find(
                    {'code': {'$in': code}, 'crawl_date': {'$in': report_date}}, batch_size=10000)]
            elif code is None and report_date is not None:
                data = [item for item in collection.find(
                    {'crawl_date': {'$in': report_date}}, batch_size=10000)]
            elif code is not None and report_date is None:
                data = [item for item in collection.find(
                    {'code': {'$in': code}}, batch_size=10000)]
            else:
                data = [item for item in collection.find()]
        else:
            print("type must be date or report")

        if len(data) > 0:
            res_pd = pd.DataFrame(data)
            if ltype in ['CH', 'CN']:

                cndict = dict(zip(num_columns, CH_columns))
                cndict['283']='283'
                try:
                    cndict['284'] = '284'
                    cndict['285'] = '285'
                    cndict['286'] = '286'
                except:
                    pass
                cndict['_id']='_id'
                cndict['code']='code'
                cndict['report_date']='report_date'
                cndict['crawl_date']='crawl_date'
                res_pd.columns = res_pd.columns.map(lambda x: cndict[x])
            elif ltype is 'EN':
                endict=dict(zip(num_columns,EN_columns))
                endict['283']='283'
                try:
                    endict['284'] = '284'
                    endict['285'] = '285'
                    endict['286'] = '286'
                except:
                    pass
                endict['_id']='_id'
                endict['code']='code'
                endict['report_date']='report_date'
                endict['crawl_date']='crawl_date'
                res_pd.columns = res_pd.columns.map(lambda x: endict[x])

            if res_pd.report_date.dtype == numpy.int64:
                res_pd.report_date = pd.to_datetime(
                    res_pd.report_date.apply(QA_util_date_int2str))
            else:
                res_pd.report_date = pd.to_datetime(res_pd.report_date)

            return res_pd.replace(-4.039810335e+34, numpy.nan).set_index(['report_date', 'code'], drop=False)
        else:
            return None
    except Exception as e:
        raise e

def QA_fetch_stock_financial_calendar(code, start, end=None, format='pd', collections=DATABASE.report_calendar):
    '获取股票日线'
    #code= [code] if isinstance(code,str) else code
    # code checking
    code = QA_util_code_tolist(code)

    if QA_util_date_valid(end):

        __data = []
        cursor = collections.find({
            'code': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                "$gte": QA_util_date_stamp(start)}}, {"_id": 0}, batch_size=10000)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.drop_duplicates(
                (['report_date', 'code']))
            res = res.ix[:, ['code', 'name', 'pre_date', 'first_date', 'second_date',
                             'third_date', 'real_date', 'codes', 'report_date', 'crawl_date']]
        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_stock_financial_calendar format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_stock_financial_calendar data parameter start=%s end=%s is not right' % (start, end))


def QA_fetch_stock_divyield(code, start, end=None, format='pd', collections=DATABASE.stock_divyield):
    '获取股票日线'
    #code= [code] if isinstance(code,str) else code
    # code checking
    code = QA_util_code_tolist(code)

    if QA_util_date_valid(end):

        __data = []
        cursor = collections.find({
            'a_stockcode': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                "$gte": QA_util_date_stamp(start)}}, {"_id": 0}, batch_size=10000)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.drop_duplicates(
                (['dir_dcl_date', 'a_stockcode']))
            res = res.ix[:, ['a_stockcode', 'a_stocksname', 'div_info', 'div_type_code', 'bonus_shr',
                             'cash_bt', 'cap_shr', 'epsp', 'ps_cr', 'ps_up', 'reg_date', 'dir_dcl_date',
                             'a_stockcode1', 'ex_divi_date', 'prg', 'report_date', 'crawl_date']]
        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_stock_divyield format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_stock_divyield data parameter start=%s end=%s is not right' % (start, end))

def QA_fetch_financial_TTM(code, start, end = None, format='pd', collections=DATABASE.financial_TTM):
    '获取财报TTM数据'
    #code= [code] if isinstance(code,str) else code
    # code checking
    code = QA_util_code_tolist(code)

    if QA_util_date_valid(end):
        __data = []

        cursor = collections.find({
            'CODE': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                "$gte": QA_util_date_stamp(start)}}, batch_size=10000)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.drop('_id', axis=1).drop_duplicates((['REPORT_DATE', 'CODE']))
        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_financial_TTM format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_financial_TTM data parameter start=%s end=%s is not right' % (start, end))

def QA_fetch_stock_fianacial(code, start, end = None, format='pd', collections=DATABASE.stock_financial_analysis):
    '获取quant基础数据'
    #code= [code] if isinstance(code,str) else code
    # code checking
    code = QA_util_code_tolist(code)
    if QA_util_date_valid(end):
        cursor = collections.find({
            'CODE': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                "$gte": QA_util_date_stamp(start)}}, batch_size=10000)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]
        res = pd.DataFrame([item for item in cursor])

        try:
            res =  res.drop('_id', axis=1).assign(DATE=pd.to_datetime(
                res.DATE, unit='ms')).drop_duplicates((['CODE', 'DATE']))
            #res.columns = [i.lower() for i in list(res.columns)]

        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            #res['report_date'] = pd.to_datetime(res['report_date']/1000, unit='s')
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_financial_TTM format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_financial_TTM data parameter start=%s end=%s is not right' % (start, end))


def QA_fetch_stock_alpha(code, start, end=None, format='pd', collections=DATABASE.stock_alpha):
    '获取股票日线'
    #code= [code] if isinstance(code,str) else code
    # code checking
    code = QA_util_code_tolist(code)

    if QA_util_date_valid(end):

        __data = []
        cursor = collections.find({
            'code': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                "$gte": QA_util_date_stamp(start)}}, {"_id": 0}, batch_size=10000)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.drop_duplicates(
                (['code', 'date']))
            res = res.ix[:, ['code', 'date', 'alpha_001',
                             'alpha_002',
                             'alpha_003',
                             'alpha_004',
                             'alpha_005',
                             'alpha_006',
                             'alpha_007',
                             'alpha_008',
                             'alpha_009',
                             'alpha_010',
                             'alpha_011',
                             'alpha_012',
                             'alpha_013',
                             'alpha_014',
                             'alpha_015',
                             'alpha_016',
                             'alpha_017',
                             'alpha_018',
                             'alpha_019',
                             'alpha_020',
                             'alpha_021',
                             'alpha_022',
                             'alpha_023',
                             'alpha_024',
                             'alpha_025',
                             'alpha_026',
                             'alpha_027',
                             'alpha_028',
                             'alpha_029',
                             'alpha_030',
                             'alpha_031',
                             'alpha_032',
                             'alpha_033',
                             'alpha_034',
                             'alpha_035',
                             'alpha_036',
                             'alpha_037',
                             'alpha_038',
                             'alpha_039',
                             'alpha_040',
                             'alpha_041',
                             'alpha_042',
                             'alpha_043',
                             'alpha_044',
                             'alpha_045',
                             'alpha_046',
                             'alpha_047',
                             'alpha_048',
                             'alpha_049',
                             'alpha_050',
                             'alpha_051',
                             'alpha_052',
                             'alpha_053',
                             'alpha_054',
                             'alpha_055',
                             'alpha_056',
                             'alpha_057',
                             'alpha_058',
                             'alpha_059',
                             'alpha_060',
                             'alpha_061',
                             'alpha_062',
                             'alpha_063',
                             'alpha_064',
                             'alpha_065',
                             'alpha_066',
                             'alpha_067',
                             'alpha_068',
                             'alpha_069',
                             'alpha_070',
                             'alpha_071',
                             'alpha_072',
                             'alpha_073',
                             'alpha_074',
                             'alpha_077',
                             'alpha_078',
                             'alpha_080',
                             'alpha_081',
                             'alpha_082',
                             'alpha_083',
                             'alpha_084',
                             'alpha_085',
                             'alpha_086',
                             'alpha_087',
                             'alpha_088',
                             'alpha_089',
                             'alpha_090',
                             'alpha_091',
                             'alpha_092',
                             'alpha_093',
                             'alpha_095',
                             'alpha_096',
                             'alpha_097',
                             'alpha_098',
                             'alpha_099',
                             'alpha_100',
                             'alpha_101',
                             'alpha_102',
                             'alpha_103',
                             'alpha_104',
                             'alpha_105',
                             'alpha_106',
                             'alpha_107',
                             'alpha_108',
                             'alpha_109',
                             'alpha_111',
                             'alpha_113',
                             'alpha_114',
                             'alpha_115',
                             'alpha_116',
                             'alpha_117',
                             'alpha_118',
                             'alpha_119',
                             'alpha_120',
                             'alpha_121',
                             'alpha_122',
                             'alpha_123',
                             'alpha_124',
                             'alpha_125',
                             'alpha_126',
                             'alpha_127',
                             'alpha_128',
                             'alpha_129',
                             'alpha_130',
                             'alpha_131',
                             'alpha_132',
                             'alpha_133',
                             'alpha_134',
                             'alpha_135',
                             'alpha_137',
                             'alpha_138',
                             'alpha_139',
                             'alpha_141',
                             'alpha_142',
                             'alpha_143',
                             'alpha_145',
                             'alpha_146',
                             'alpha_147',
                             'alpha_148',
                             'alpha_149',
                             'alpha_150',
                             'alpha_151',
                             'alpha_152',
                             'alpha_153',
                             'alpha_154',
                             'alpha_155',
                             'alpha_156',
                             'alpha_158',
                             'alpha_159',
                             'alpha_160',
                             'alpha_161',
                             'alpha_162',
                             'alpha_163',
                             'alpha_164',
                             'alpha_165',
                             'alpha_166',
                             'alpha_167',
                             'alpha_168',
                             'alpha_169',
                             'alpha_170',
                             'alpha_171',
                             'alpha_172',
                             'alpha_173',
                             'alpha_175',
                             'alpha_176',
                             'alpha_177',
                             'alpha_178',
                             'alpha_179',
                             'alpha_180',
                             'alpha_181',
                             'alpha_182',
                             'alpha_183',
                             'alpha_184',
                             'alpha_185',
                             'alpha_186',
                             'alpha_187',
                             'alpha_188',
                             'alpha_189',
                             'alpha_190',
                             'alpha_191']]
        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_stock_alpha format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_stock_alpha data parameter start=%s end=%s is not right' % (start, end))