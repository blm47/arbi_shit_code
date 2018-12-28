#!/usr/bin/python3
import os
import time
import json
from datetime import datetime
import random
import MarketClass
import threading
import sys
#Создаем лог файл______
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
def log(*args):
    LOG_FILE = CURR_DIR + '/logs/' + 'orderbook_log.txt'
    try:
        l = open(LOG_FILE, 'a')
        print(datetime.now(), *args)
        print(datetime.now(), *args, file=l)
        l.close()
    except Exception as oshibka:
        print('Ошибка при записи лога!', oshibka)
        pass

def write_orderbook(market, para, data):
    orderbooks = CURR_DIR + '/orderbooks/' + market + para + '.txt'
    try:
        lr = open(orderbooks, 'r')
        lr.readline()
        readdata = json.loads(str(lr.readline()))
        lr.close()
        if readdata != data:
            l = open(orderbooks, 'w')
            print(round(time.time(), 2), file=l)
            l.write(json.dumps(data))
            l.close()
        else:
            pass
    except FileNotFoundError:
        l = open(orderbooks, 'w')
        l.close()
    except json.decoder.JSONDecodeError:
        #lr.close()
        l = open(orderbooks, 'w')
        print(round(time.time(), 2), file=l)
        l.write(json.dumps(data))
        l.close()
    except Exception as oshibka:
        log('Ошибка при записи книги!', oshibka)
        pass

def get_orders_books(para, x):
    check = int(time.time()) + x
    count_stat = 0
    while check > int(time.time()):
        time.sleep(0.07)
        if count_stat == 0 or count_stat < round(time.time()):
            print(datetime.now(), para['Poloniex'], ' Working...')
            count_stat = round(time.time()) + 23

        try:
            if para['Exmo'] != "":
                order_book_exmo = Exmo.orderbook(para['Exmo'])[para['Exmo']]
        except TypeError as err:
            print(datetime.now(),'Книга Exmo не поучена', err)
            order_book_exmo = 0
            pass
        except KeyError as err:
            print(datetime.now(),'На Exmo нет такой пары', err)
            order_book_exmo = 0
            pass
        write_orderbook(Exmo.name, para['Exmo'], order_book_exmo)

        order_book_poloniex = Poloniex.orderbook(para['Poloniex'])
        write_orderbook(Poloniex.name, para['Poloniex'], order_book_poloniex)

        # try:
        #     order_book_wex = Wex.orderbook(para['Wex'])[para['Wex']]
        #     write_orderbook(Wex.name, para['Wex'], order_book_wex)
        # except KeyError as err:
        #     print(datetime.now(),'Книга Wex не поучена', err)
        #     order_book_wex = 0
        #     pass
        # except TypeError as err:
        #     print(datetime.now(),'Книга Wex не поучена', err)
        #     order_book_wex = 0
        #     pass
        # pass
    print(datetime.now(),'Выход из функции')

Poloniex = MarketClass.Poloniex('Poloniex','asd','asdf')
Exmo = MarketClass.Exmo('Exmo','asd','asdf')
Bitfinex = MarketClass.Bitfinex('Bitfinex','asd','asdf')
Wex = MarketClass.Wex('Wex','asd','asdf')

work_pairs = MarketClass.work_pairs
# work_pairs = [{'Poloniex': 'BTC_ZEC', 'Exmo': 'ZEC_BTC', 'Bitfinex': 'zecbtc', 'Wex': 'zec_btc'},
#               {'Poloniex': 'BTC_XRP', 'Exmo': 'XRP_BTC', 'Bitfinex': 'xrpbtc'},
#               {'Poloniex': 'BTC_BCH', 'Exmo': 'BCH_BTC', 'Bitfinex': 'bchbtc', 'Wex': 'bch_btc'},
#               {'Poloniex': 'BTC_ETH', 'Exmo': 'ETH_BTC', 'Bitfinex': 'ethbtc', 'Wex': 'eth_btc'},
#               {'Poloniex': 'BTC_DOGE', 'Exmo': 'DOGE_BTC', 'Bitfinex': 'dogebtc'},
#               {'Poloniex': 'BTC_ETC', 'Exmo': 'ETC_BTC', 'Bitfinex': 'etcbtc'}]
#number = input('Введите номер виртуалки: ')
number=sys.argv[1]
print(number)

if int(number) == 1:
    work = work_pairs[0:4]
elif int(number) == 2:
    work = work_pairs[4:9]
elif int(number) == 3:
    work = work_pairs[-3:]
time.sleep((random.randint(1,10) / 5))
#Получаем книги ордеров:_____
while True:
    print(datetime.now(),'Количество активных потоков ',threading.activeCount())
    for i in work:
        threading.Thread(target=get_orders_books,args=[i,3600]).start()
    print(datetime.now(),'Количество активных потоков ', threading.activeCount())
    time.sleep(3600)
    pass
