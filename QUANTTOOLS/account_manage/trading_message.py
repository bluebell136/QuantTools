from QUANTTOOLS.message_func.wechat import send_actionnotice

def send_trading_message(account1, strategy_id, account_info, code, NAME, INDUSTRY, mark, direction, type, priceType, price, client):
    codes = []
    try:
        if direction == 'SELL':
            if type == 'MARKET':
                client.sell(account1, symbol=code, type=type, priceType=priceType, amount=abs(mark))
            elif type == 'LIMIT':
                client.sell(account1, symbol=code, type=type, amount=abs(mark) , price = price)
            else:
                pass
        elif direction == 'BUY':
            if type == 'MARKET':
                client.buy(account1, symbol=code, type=type, priceType=priceType, amount=abs(mark))
            elif type == 'LIMIT':
                client.buy(account1, symbol=code, type=type, amount=abs(mark) , price = price)
            else:
                pass
        elif direction == 'HOLD':
            pass
        send_actionnotice(strategy_id,
                          account_info,
                          '{code}({NAME},{INDUSTRY})'.format(code=code,NAME= NAME, INDUSTRY=INDUSTRY),
                          direction = direction,
                          offset='OPEN',
                          volume=abs(mark),
                          price = price
                          )
    except Exception as e:
        send_actionnotice(strategy_id,
                          account_info,
                          '{code}({NAME},{INDUSTRY}) 交易失败'.format(code=code,NAME= NAME, INDUSTRY=INDUSTRY),
                          direction = direction,
                          offset= 'OPEN',
                          volume=abs(mark)
                          )
        print(e)
        codes.append(code)
    return(codes)