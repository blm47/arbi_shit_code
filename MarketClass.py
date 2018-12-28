#!/usr/bin/python3
# ! _*_ coding: UTF-8 _*_
# 27/12 Убрал time_sleeps's у функций call_api
# 01/01/2018 убрал зацикленность на получение книги ордеров
# 08/01/2018 Функции chek_and_close_open_orders добавил возврат списка потерь в % с каждого отмененного ордера
# 06/02/2018 У функции call_api (EXMO) убрал зацикленность отправки запроса
import os
import time
import json
import sqlite3
import requests
import urllib.request, http.client
# эти модули нужны для генерации подписи API
import hmac, hashlib

from urllib.parse import urlparse
from datetime import datetime
from datetime import timedelta
import threading
from configobj import ConfigObj

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
configs = ConfigObj('configs.conf')

def log_close_order(*args):
    LOG_FILE = CURR_DIR + '/logs/' + 'close_orders_log.txt'
    try:
        l = open(LOG_FILE, 'a')
        print(datetime.now(), *args)
        print(datetime.now(), *args, file=l)
        l.close()
    except Exception as oshibka:
        print('Ошибка при записи лога!', str(oshibka))
        pass

class DataBase:
    def __init__(self, name, place):
        self.name = name
        self.place = place

    def query(self, *kwarg):
        results = None
        conn = sqlite3.connect(self.place)
        cursor = conn.cursor()
        try:
            # Делаем SELECT запрос к базе данных, используя обычный SQL-синтаксис
            cursor.execute(*kwarg)
            results = cursor.fetchall()
            if conn:
                conn.commit()
                conn.close()
        except Exception as err:
            print('Error: ', err)
            pass
        #finally:
            #if conn:
                #conn.commit()
                #conn.close()
        # print(results)
        return results

    def create(self):
        prepare1 = """
          create table if not exists
            trades (
              account_name TEXT,
              order_pair TEXT,
              buy_market TEXT,
              sell_market TEXT,
              buy_amount REAL,
              buy_price REAL,
              buy_summary_amount REAL,
              buy_created DATETIME,

              sell_amount REAL,
              sell_price REAL,
              sell_summary_amount REAL,
              sell_created DATETIME,

              profit_summ REAL,
              profit_procent REAL
            );
        """
        prepare2 = """
                  create table if not exists
                    close_orders (
                      account_name TEXT,
                      market TEXT,
                      order_pair TEXT,
                      order_type TEXT,
                      amount REAL,
                      old_price REAL,
                      old_summary_amount REAL,
                      old_time_created DATETIME,

                      new_price REAL,
                      new_summary_amount REAL,
                      new_time_created DATETIME,

                      deprofit_summ REAL,
                      deprofit_procent REAL
                    );
                """
        prepare3 = """
                  create table if not exists
                    logs_lose_trades (
                      account_name TEXT,
                      pair TEXT,
                      market1 TEXT,
                      price1 REAL,
                      amount1 REAL,
                      total_amount1 REAL,
                      cur_bal1 REAL,

                      market2 TEXT,
                      price2 REAL,
                      total_amount2 REAL,
                      cur_bal2 REAL,

                      curr_time DATETIME,

                      lose_profit_summ REAL
                    );
                """
        prepare4 = """
                  create table if not exists
                    orders_greate_failed (
                      account_name TEXT,
                      pair TEXT,
                      market TEXT,
                      ord_type TEXT,
                      price REAL,
                      amount REAL,
                      total_amount REAL,

                      cur_time DATETIME
                    );
                """
        prepare5 = """
                  create table if not exists
                    balans_log (
                      account_name TEXT,
                      cur_time DATETIME,
                      all_balanses TEXT,
                      comment TEXT
                  );
            """
        # all_balanses {birja: {valuta: 'kol-vo', ...}, ...}
        prepare6 = """
                    create table if not exists
                        balans_changes (
                          account_name TEXT,
                          cur_time DATETIME,
                          market TEXT,
                          currency TEXT,
                          amount REAL,

                          comment TEXT

                  );
            """
        prepare7 = """
                    create table if not exists
                        human_trades (
                          account_name TEXT,
                          cur_time DATETIME,
                          currency1 TEXT,
                          currency2 TEXT,
                          amount REAL,
                          price REAL,
                          total_currency1 REAL,
                          total_currency2 REAL,


                          comment TEXT

                  );
            """  # comment = TEXT {type: 'sell', valuta: 'BTC'}
        self.query(prepare1)
        self.query(prepare2)
        self.query(prepare3)
        self.query(prepare4)
        self.query(prepare5)
        self.query(prepare6)
        self.query(prepare7)
        pass

    def read(self,tabl,dic): # dic = {'account_name': 'blm','cur_time':'2018-01-22%'}
        ysloviya = ""
        for i in dic:
            if str(dic[i]).find('%') == -1:
                ysloviya += i + " = '" + str(dic[i]) + "' and "
            else:
                ysloviya += i + " LIKE '" + str(dic[i]) + "' and "

        sql = """SELECT * FROM {tabl} WHERE {ysloviya}""".format(tabl=tabl,ysloviya=ysloviya[:-5])
        # print(sql)
        return self.query(sql)
        pass

    def write(self,tabl,dic): #dic = {'account_name': 'blm', 'market': 'Poloniex', 'para': 'BTC_ZEC', 'type': 'buy', 'cur_time': str(datetime.now())[:str(datetime.now()).find('.')]
        polya = []
        values = []
        for i in dic: #{'pole': values, ...}
            polya.append(str(i))
            values.append(str(dic[i]))
        sql = """insert into {tabl} ({polya}) VALUES {values}""".format(tabl= tabl, polya= ','.join(polya), values= tuple(values))
        self.query(sql)
        return sql

    def delite(self,tabl,dic): #dic = {'account_name': 'blm','cur_time':'2018-01-22%'}
        ysloviya = ""
        for i in dic:
            if str(dic[i]).find('%') == -1:
                ysloviya += i + " = '" + str(dic[i]) + "' and "
            else:
                ysloviya += i + " LIKE '" + str(dic[i]) + "' and "
        sql = """DELETE FROM {tabl} WHERE {ysloviya}""".format(tabl=tabl,ysloviya=ysloviya[:-5])
        #print(sql)
        return self.query(sql)
        pass

    def update(self,tabl,dic): #dic = {'set': {'field': 'value', 'field': 'value', }, 'where': {'field': 'value', 'field': 'value', }}
        set = ""
        where = ""
        for i in dic['set']:
            if str(dic['set'][i]).find('%') == -1:
                set += i + " = '" + str(dic['set'][i]) + "' , "
            else:
                set += i + " LIKE '" + str(dic['set'][i]) + "' , "
        for i in dic['where']:
            if str(dic['where'][i]).find('%') == -1:
                where += i + " = '" + str(dic['where'][i]) + "' and "
            else:
                where += i + " LIKE '" + str(dic['where'][i]) + "' and "
        sql = """UPDATE {tabl} SET {set} WHERE {where}""".format(tabl=tabl,set=set[:-3], where=where[:-5])
        #print(sql)
        return self.query(sql)
        pass

    def clear(self, period_e=datetime.now()):
        tables = ['logs_lose_trades', 'balans_log']
        dates = []
        for i in range(1, period_e.month - 2):
            if i < 10:
                dates.append(str(period_e.year) + '-0' + str(i) + '%')
            else:
                dates.append(str(period_e.year) + '-' + str(i) + '%')
        for t in tables:
            for d in dates:
                self.delite(t,{'cur_time': d})
                self.delite(t, {'curr_time': d})

bd = DataBase('local','local.db')
bd.create()
#Создаем классы бирж:
class Livecoin:
    def __init__(self, name, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.name = name
        self.fee = 0.002
        self.Withdrawal_fee = {'BTC': 0.0001, 'ZEC': 0.001, 'BCH': 0.0001, 'ETH': 0.005, 'LTC': 0.001, 'XRP': 0.15, 'DASH': 0.01, 'ETC': 0.01, 'DOGE': 5, 'XMR': 0.01}
        self.time_zone = -3  # Время на бирже отличается от текущего в часах

    def call_api(self, api_url='https://api.livecoin.net/', http_method="POST", **kwargs): #Переписал но не тестил
        #time.sleep(0.17)  # По правилам биржи нельзя больше 6 запросов в секунду
        #payload = {'nonce': int(round(time.time() * 1000))}

        if kwargs:
            payload = kwargs
        payload = urllib.parse.urlencode(payload)

        H = hmac.new(key=self.API_SECRET, digestmod=hashlib.sha256)
        H.update(payload.encode('utf-8'))
        H.hexdigest()
        sign = H.upper()

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self.API_KEY,
                   "Sign": sign}

        url_o = urlparse(api_url)
        conn = http.client.HTTPSConnection(url_o.netloc)
        conn.request(http_method, api_url, payload, headers)
        response = conn.getresponse().read()

        conn.close()
        try:
            obj = json.loads(response.decode('utf-8'))
            obj.update({'Res': ''})
        except Exception as err:
            obj = {'error': err}
        try:
            if obj['error'] != '':
                obj.update({'Res':'False'})
        except KeyError:
            pass
        if obj['Res'] == '':
            obj.update({'Res': 'True'})
        return obj

    def orderbook(self,para):
        try:
            r = requests.get('https://poloniex.com/public?command=returnOrderBook&currencyPair=' + para)
            return r.json()
        except Exception:
            return 0
            pass

    def readorderbooks(self,market,para):
        try:
            ob = open((CURR_DIR + '/orderbooks/' + market + para + '.txt'), 'r')
            timestamp = float(ob.readline()) + 0.47
            if timestamp > round(time.time(), 2):
                data = json.loads(str(ob.readline()))
                ob.close()
            else:
                ob.close()
                return 0
        except ValueError as err:
            print('ValueError',err)
            return 0
        except FileNotFoundError as err:
            print('FileNotFoundError',err)
            return 0
        return data


    def order_sell(self, summ,para,price):
        rezult = self.call_api(command='sell', currencyPair=para, amount=summ, rate=price)
        return  rezult
    def order_buy(self, summ,para,price):
        rezult = self.call_api(command='buy', currencyPair=para, amount=summ, rate=price)
        return  rezult

    def cancelOrder(self, orderNumber):
        rezult = self.call_api(command='cancelOrder', orderNumber=orderNumber)
        return  rezult

    def returnOpenOrders(self,para='all'):
        return self.call_api(command='returnOpenOrders', currencyPair=para)

    def chek_and_close_open_orders(self,pair,order_book):
        open_orders = self.returnOpenOrders()
        ret = []
        if order_book != 0 and open_orders['Res'] != 'False':
            for i in open_orders:  # i - пара, open_orders[i] - инфо об ордерах по данной паре
                if i == pair:
                    # ОТменяем каждый висящий ордер
                    for ord in open_orders[i]:
                        log_close_order('На ', self.name, 'Найден ордер: ', ord)
                        if ord['type'] == 'buy':  # Определяем тип ордера, отменяем и выставляем новый
                            if float(ord['rate']) < float(order_book['bids'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['bids'][0][0]) * 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['orderNumber'])
                                neworder = self.order_buy(ord['amount'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 больше чем в первом bids
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                ret.append(round((((rate / float(ord['rate'])) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Спрос из кнги:', order_book['bids'][0][0])
                        elif ord['type'] == 'sell':
                            if float(ord['rate']) > float(order_book['asks'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['asks'][0][0]) / 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['orderNumber'])
                                neworder = self.order_sell(ord['amount'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 меньше чем в первом asks
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                ret.append(round((((float(ord['rate']) / rate) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Предложение из кнги:', order_book['asks'][0][0])
                        else:
                            log_close_order('Не удалось определить тип ордера. Ничего не делаю')
            return ret
        else:
            print('Получить ордера на Poloniex НЕ УДАЛОСЬ!!!!!')
            return 0

    def skolko_mojno_kypit(self, summ, order_book_poloniex):  # Сумма в ПЕРВОЙ валюте, order_book_poloniex от валютной пары
        kypit = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_poloniex != 0:
            for i in order_book_poloniex["asks"]:
                if (float(i[0]) * float(i[1]) < summ):
                    kypit += float(i[1]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * fee
                    summ -= float(i[0]) * float(i[1])
                else:
                    kypit += summ / float(i[0]) * (1 - fee)
                    zaplatim_fee += summ / float(i[0]) * fee
                    break
            return [kypit, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

    def na_skolko_mojno_prodat(self, summ, order_book_poloniex):  # Сумма во ВТОРОЙ валюте, order_book_poloniex от валютной пары
        prod = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_poloniex != 0:
            for i in order_book_poloniex["bids"]:
                if (float(i[1]) < summ):
                    prod += float(i[1]) * float(i[0]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * float(i[0]) * fee
                    summ -= float(i[1])
                else:
                    prod += summ * float(i[0]) * (1 - fee)
                    zaplatim_fee += summ * float(i[0]) * fee
                    break
            return [prod, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

class Poloniex:
    def __init__(self, name, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET.encode()
        self.name = name
        self.fee = 0.001
        self.Withdrawal_fee = {'BTC': 0.0001, 'ZEC': 0.001, 'BCH': 0.0001, 'ETH': 0.005, 'LTC': 0.001, 'XRP': 0.15, 'DASH': 0.01, 'ETC': 0.01, 'DOGE': 5, 'XMR': 0.015}
        self.time_zone = -3  # Время на бирже отличается от текущего в часах -3 от текущего

    def call_api(self, api_url='https://poloniex.com/tradingApi', http_method="POST", **kwargs):
        #time.sleep(0.17)  # По правилам биржи нельзя больше 6 запросов в секунду
        payload = {'nonce': int(round(time.time() * 1000))}

        if kwargs:
            payload.update(kwargs)
        payload = urllib.parse.urlencode(payload)

        H = hmac.new(key=self.API_SECRET, digestmod=hashlib.sha512)
        H.update(payload.encode('utf-8'))
        sign = H.hexdigest()

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self.API_KEY,
                   "Sign": sign}

        url_o = urlparse(api_url)
        conn = http.client.HTTPSConnection(url_o.netloc)
        conn.request(http_method, api_url, payload, headers)
        response = conn.getresponse().read()

        conn.close()
        try:
            obj = json.loads(response.decode('utf-8'))
            obj.update({'Res': ''})
        except Exception as err:
            obj = {'error': err}
        try:
            if obj['error'] != '':
                obj.update({'Res':'False'})
        except KeyError:
            pass
        if obj['Res'] == '':
            obj.update({'Res': 'True'})
        return obj

    def orderbook(self,para):
        try:
            r = requests.get('https://poloniex.com/public?command=returnOrderBook&currencyPair=' + para)
            return r.json()
        except Exception:
            return 0
            pass

    def readorderbooks(self,market,para):
        try:
            ob = open((CURR_DIR + '/orderbooks/' + market + para + '.txt'), 'r')
            timestamp = float(ob.readline()) + 3.97
            if timestamp > round(time.time(), 2):
                data = json.loads(str(ob.readline()))
                ob.close()
            else:
                ob.close()
                return 0
        except ValueError as err:
            print('ValueError on readorderbooks',err)
            return 0
        except FileNotFoundError as err:
            print('FileNotFoundError on readorderbooks',err)
            return 0
        except PermissionError as err:
            print('PermissionError on readorderbooks',err)
            return 0
        return data

    def balans(self):
        return self.call_api(command="returnBalances")

    def balans_available (self):
        return self.call_api(command="returnAvailableAccountBalances")

    def order_sell(self, summ,para,price, postOnly=False):
        if postOnly:
            rezult = self.call_api(command='sell', currencyPair=para, amount=summ, rate=price, postOnly=1)
        else:
            rezult = self.call_api(command='sell', currencyPair=para, amount=summ, rate=price)
        return  rezult
    def order_buy(self, summ,para,price, postOnly=False):
        if postOnly:
            rezult = self.call_api(command='buy', currencyPair=para, amount=summ, rate=price, postOnly=1)
        else:
            rezult = self.call_api(command='buy', currencyPair=para, amount=summ, rate=price)
        return  rezult

    def move_order(self, orderNumber, price, postOnly=False):
        if postOnly:
            rezult = self.call_api(command='moveOrder', orderNumber=orderNumber, rate=price, postOnly=1)
        else:
            rezult = self.call_api(command='moveOrder', orderNumber=orderNumber, rate=price)
        return  rezult

    def cancelOrder(self, orderNumber):
        rezult = self.call_api(command='cancelOrder', orderNumber=orderNumber)
        return  rezult

    def returnOpenOrders(self,para='all'):
        return self.call_api(command='returnOpenOrders', currencyPair=para)

    def chek_and_close_open_orders(self,pair,order_book,account_name):
        open_orders = self.returnOpenOrders()
        ret = []
        if order_book != 0 and open_orders['Res'] != 'False':
            for i in open_orders:  # i - пара, open_orders[i] - инфо об ордерах по данной паре
                if i == pair:
                    # ОТменяем каждый висящий ордер
                    for ord in open_orders[i]:
                        log_close_order('На ', self.name, 'Найден ордер: ', ord)
                        if ord['type'] == 'buy':  # Определяем тип ордера, отменяем и выставляем новый
                            if float(ord['rate']) < float(order_book['bids'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['bids'][0][0]) * 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['orderNumber'])
                                neworder = self.order_buy(ord['amount'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 больше чем в первом bids
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name':account_name,'market':self.name,'order_pair':pair,'order_type':ord['type'],'amount':ord['amount'],'old_price':ord['rate'],
                                                         'old_summary_amount':ord['total'],'old_time_created':(datetime.strptime(ord['date'], '%Y-%m-%d %H:%M:%S') - timedelta(0, 0, 0, 0, 0, self.time_zone)),
                                         'new_price':rate,'new_summary_amount':(round((rate*float(ord['amount'])),8)),
                                                         'new_time_created':str(datetime.now())[:str(datetime.now()).find('.')],'deprofit_summ':round(((rate*float(ord['amount'])) - float(ord['total'])),8),
                                                         'deprofit_procent':(round((((rate / float(ord['rate'])) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders',dic)
                                ret.append(round((((rate / float(ord['rate'])) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Спрос из кнги:', order_book['bids'][0][0])
                        elif ord['type'] == 'sell':
                            if float(ord['rate']) / 1.01 > float(order_book['asks'][0][0]):  # Проверяем что текущая цена не превышает изенение в 1% от цены ордера
                                pass

                                # bd.write('orders_greate_failed',
                                #          {'account_name': account_name, 'pair': i, 'market': self.name, #Пара нужна с полоникса а передается по текущей бирже
                                #           'ord_type': 'sell', 'price': ord['rate'], 'amount': ord['amount'],
                                #           'total_amount': ord['total'], 'cur_time': str(datetime.now())[:str(datetime.now()).find('.')]})
                                # self.cancelOrder(ord['orderNumber'])

                            elif float(ord['rate']) > float(order_book['asks'][0][0]): # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['asks'][0][0]) / 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['orderNumber'])
                                neworder = self.order_sell(ord['amount'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 меньше чем в первом asks
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name': account_name, 'market': self.name, 'order_pair': pair,
                                          'order_type': ord['type'], 'amount': ord['amount'], 'old_price': ord['rate'],
                                          'old_summary_amount': ord['total'], 'old_time_created': (datetime.strptime(ord['date'], '%Y-%m-%d %H:%M:%S') - timedelta(0, 0, 0, 0, 0, self.time_zone)),
                                          'new_price': rate, 'new_summary_amount': (round((rate * float(ord['amount'])), 8)),
                                          'new_time_created': str(datetime.now())[:str(datetime.now()).find('.')],
                                          'deprofit_summ': round((float(ord['total']) - (rate * float(ord['amount']))),8),
                                          'deprofit_procent': (round((((float(ord['rate']) / rate) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders',dic)
                                ret.append(round((((float(ord['rate']) / rate) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Предложение из кнги:', order_book['asks'][0][0])
                        else:
                            log_close_order('Не удалось определить тип ордера. Ничего не делаю')
            return ret
        else:
            print('Получить ордера на Poloniex НЕ УДАЛОСЬ!!!!!')
            return 0

    def last_bid_ask(self,order_book):
        return {'bid':order_book['bids'][0][0],'ask':order_book['asks'][0][0]}

    def get_cur_best_price(self,type, pair, best=False):
        ob = 0
        while ob == 0:
            ob = self.readorderbooks(self.name, pair)
        if best:
            if type == 'sell':
                return round(float(self.last_bid_ask(ob)['ask']) / 1.000003, 8)
            if type == 'buy':
                return round(float(self.last_bid_ask(ob)['bid']) * 1.000003, 8)
            else:
                print('Incorrect order type')
                raise ValueError
        else:
            if type == 'sell':
                return round(float(self.last_bid_ask(ob)['bid']) * 1.000003, 8)
            if type == 'buy':
                return round(float(self.last_bid_ask(ob)['ask']) / 1.000003, 8)
            else:
                print('Incorrect order type')
                raise ValueError

    def open_order(self, type, amount, pair, best=False):
        try:
            for x in range(42):
                price = self.get_cur_best_price(type,pair,best=best)
                if type == 'sell':
                    order_number = self.order_sell(amount, pair, price, postOnly=True)
                elif type == 'buy':
                    order_number = self.order_buy(amount, pair, price, postOnly=True)
                if order_number['Res'] == 'True':
                    order_number = order_number['orderNumber']
                    for i in range(60*60):
                        time.sleep(1)
                        for x in range(20):
                            open_orders = self.returnOpenOrders()
                            if open_orders['Res'] == 'True':
                                break
                            else:
                                print('Get open orders FAIL: {}'.format(open_orders))
                                time.sleep(10)
                        if open_orders[pair] == []:
                            print('Not find open orders, exit')
                            break
                        for ord in open_orders[pair]:
                            if ord['orderNumber'] == order_number:
                                price = self.get_cur_best_price(type, pair,best=best)
                                if float(ord['rate']) != price:
                                    order_number = self.move_order(order_number, price)
                                    try:
                                        order_number = order_number['orderNumber']
                                        print('New order: {}'.format(order_number))
                                    except KeyError:
                                        print("Can't update order", order_number)

                    break
                elif order_number['error'] == 'Unable to place post-only order at this price.':
                    time.sleep(10)
                    continue
                else:
                    print('Order greate FAIL: {}'.format(order_number))
                    time.sleep(10)

        except Exception as err:
            print('Error in open_order: {}, {} , {}'.format(type,amount,pair), err)


    def skolko_mojno_kypit(self, summ, order_book_poloniex):  # Сумма в ПЕРВОЙ валюте, order_book_poloniex от валютной пары
        kypit = 0
        fee = self.fee
        zaplatim_fee = 0
        i = [0]
        if order_book_poloniex != 0:
            for i in order_book_poloniex["asks"]:
                if (float(i[0]) * float(i[1]) < summ):
                    kypit += float(i[1]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * fee
                    summ -= float(i[0]) * float(i[1])
                else:
                    kypit += summ / float(i[0]) * (1 - fee)
                    zaplatim_fee += summ / float(i[0]) * fee
                    break
            return [kypit, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

    def na_skolko_mojno_prodat(self, summ, order_book_poloniex):  # Сумма во ВТОРОЙ валюте, order_book_poloniex от валютной пары
        prod = 0
        fee = self.fee
        zaplatim_fee = 0
        i = [0]
        if order_book_poloniex != 0:
            for i in order_book_poloniex["bids"]:
                if (float(i[1]) < summ):
                    prod += float(i[1]) * float(i[0]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * float(i[0]) * fee
                    summ -= float(i[1])
                else:
                    prod += summ * float(i[0]) * (1 - fee)
                    zaplatim_fee += summ * float(i[0]) * fee
                    break
            return [prod, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

class Exmo: # Подумать как реализовать перезапрос call_api
    def __init__(self, name, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET.encode()
        self.name = name
        self.API_URL='api.exmo.com'
        self.API_VERSION='v1'
        self.fee = 0.002
        self.Withdrawal_fee = {'BTC': 0.001, 'ZEC': 0.001, 'BCH': 0.001, 'ETH': 0.01, 'LTC': 0.01, 'XRP': 0.02, 'DASH': 0.01, 'ETC': 0.01, 'DOGE': 1, 'XMR': 0.05}
        self.time_zone = -3 #на сколько отличается время на бирже в часа -3 от текущего
        self.pairs_exmo = "DASH_BTC,ZEC_BTC,ETH_BTC,ETH_LTC,ETC_BTC,LTC_BTC,XRP_BTC,XMR_BTC,BTC_USDT,ETH_USDT,DOGE_BTC,WAVES_BTC,KICK_BTC,KICK_ETH,BTC_RUB,BCH_BTC"

    def call_api(self, api_method, http_method="POST", **kwargs):
        #time.sleep(0.34)  # По правилам биржи нельзя больше 3 запросов в секунду
        payload = {'nonce': int(round(time.time() * 1000))}

        if kwargs:
            payload.update(kwargs)
        payload = urllib.parse.urlencode(payload)

        H = hmac.new(key=self.API_SECRET, digestmod=hashlib.sha512)
        H.update(payload.encode('utf-8'))
        sign = H.hexdigest()

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self.API_KEY,
                   "Sign": sign}
        try:
            print(datetime.now(),'Посылаю запрос на Exmo...')
            conn = http.client.HTTPSConnection('api.exmo.com')
            conn.request(http_method, "/" + 'v1' + "/" + api_method, payload, headers)
            response = conn.getresponse().read()
            conn.close()
            obj = json.loads(response.decode('utf-8'))
            print(datetime.now(),'Ответ получил от Exmo, прерываю')
        except Exception:
            obj={}
        obj.update({'Res': ''})
        try:
            if obj['error'] != '': #{'result': False, 'Res': 'False', 'error': '40009: The nonce parameter is less or equal than what was used before "1517580076410"'}
                obj.update({'Res':'False'})
        except KeyError:
            pass
        if obj['Res'] == '':
            obj.update({'Res': 'True'})
        return obj

    def orderbook(self,para):
        try:
            #print(datetime.now(),'Пытаюсь получить книгу ордеров с Ексмо...')
            #time.sleep(0.35) # По правилам биржи нельзя больше 180 запросов в минуту
            r = requests.get('https://api.exmo.com/v1/order_book/?pair=' + para, timeout=0.6)
            return r.json()
            #print(datetime.now(), 'Книга получена с Ексмо, возвращаю:')
        except Exception:
            return 0
            pass #continue

    def readorderbooks(self,market,para):
        try:
            ob = open((CURR_DIR + '/orderbooks/' + market + para + '.txt'), 'r')
            asd = ob.readline()
            #print(asd)
            timestamp = float(asd) + 3.97
            if timestamp > round(time.time(), 2):
                data = json.loads(str(ob.readline()))
                ob.close()
            else:
                ob.close()
                return 0
        except ValueError as err:
            print(datetime.now(), 'ValueError', err)
            return 0
        except FileNotFoundError as err:
            print('FileNotFoundError', err)
            return 0
        return data

    def order_sell(self, summ,para,price):
        rezult = self.call_api('order_create', pair=para, quantity = summ, price=price, type='sell')
        return  rezult
    def order_buy(self, summ,para,price):
        rezult = self.call_api('order_create', pair=para, quantity = summ, price=price, type='buy')
        return  rezult

    def cancelOrder(self, orderNumber):
        rezult = self.call_api('order_cancel', order_id=orderNumber)
        return  rezult

    def returnOpenOrders(self):
        return self.call_api('user_open_orders')

    def chek_and_close_open_orders(self, pair, order_book,account_name):
        open_orders = self.returnOpenOrders()
        ret = []
        if order_book != 0 and open_orders['Res'] != 'False':
            for i in open_orders:  # i - пара, open_orders[i] - инфо об ордерах по данной паре
                if i == pair:
                    # ОТменяем каждый висящий ордер по i-ой паре
                    for ord in open_orders[i]:
                        log_close_order('На ', self.name, 'Найден ордер: ', ord)
                        if ord['type'] == 'buy':  # Определяем тип ордера, отменяем и выставляем новый
                            if float(ord['price']) < float(order_book['bid'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['bid'][0][0]) * 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['order_id'])
                                neworder = self.order_buy(ord['quantity'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 больше чем в первом bids
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name': account_name, 'market': self.name, 'order_pair': pair,
                                          'order_type': ord['type'], 'amount': ord['quantity'], 'old_price': ord['price'],
                                          'old_summary_amount': ord['amount'], 'old_time_created': datetime.fromtimestamp(int(ord['created'])).strftime('%Y-%m-%d %H:%M:%S'),
                                          'new_price': rate, 'new_summary_amount': (round((rate * float(ord['quantity'])), 8)),
                                          'new_time_created': str(datetime.now())[:str(datetime.now()).find('.')],
                                          'deprofit_summ': ((round((rate * float(ord['quantity'])), 8)) - float(ord['amount'])),
                                          'deprofit_procent': (round((((rate / float(ord['price'])) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders', dic)
                                ret.append(round((((rate / float(ord['price'])) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Спрос из кнги:', order_book['bid'][0][0])
                        elif ord['type'] == 'sell':
                            if float(ord['price']) > float(order_book['ask'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['ask'][0][0]) / 1.000003, 8)
                                cancelorder = self.cancelOrder(ord['order_id'])
                                neworder = self.order_sell(ord['quantity'], i, rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 меньше чем в первом asks
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name': account_name, 'market': self.name, 'order_pair': pair,
                                          'order_type': ord['type'], 'amount': ord['quantity'], 'old_price': ord['price'],
                                          'old_summary_amount': ord['amount'], 'old_time_created': datetime.fromtimestamp(int(ord['created'])).strftime('%Y-%m-%d %H:%M:%S'),
                                          'new_price': rate, 'new_summary_amount': (round((rate * float(ord['quantity'])), 8)),
                                          'new_time_created': str(datetime.now())[:str(datetime.now()).find('.')],
                                          'deprofit_summ': (float(ord['amount']) - (round((rate * float(ord['quantity'])), 8))),
                                          'deprofit_procent': (round((((float(ord['price']) / rate) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders', dic)
                                ret.append(round((((float(ord['price']) / rate) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Предложение из кнги:', order_book['ask'][0][0])
                        else:
                            log_close_order('Не удалось определить тип ордера. Ничего не делаю')
            return ret
        else:
            print('Получить ордера на Exmo НЕ УДАЛОСЬ!!!!!')
            return 0

    def last_bid_ask(self,order_book):
        return {'bid':order_book['bid'][0][0],'ask':order_book['ask'][0][0]}

    def skolko_mojno_kypit(self, summ, order_book_exmo):  # Сумма в валюте на которую покупаем, она спишется и должна быть на балансе
        kypit = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_exmo != 0:
            for i in order_book_exmo["ask"]:
                if (float(i[0]) * float(i[1]) < summ):
                    kypit += float(i[1]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * fee
                    summ -= float(i[0]) * float(i[1])
                else:
                    kypit += summ / float(i[0]) * (1 - fee)
                    zaplatim_fee += summ / float(i[0]) * fee
                    break
            return [kypit, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

    def na_skolko_mojno_prodat(self, summ, order_book_exmo):  # Сумма в валюте которую продаем, она спишется и должна быть на балансе
        prod = 0
        fee = self.fee
        zaplatim_fee = 0
        for i in order_book_exmo["bid"]:
            if (float(i[1]) < summ):
                prod += float(i[1]) * float(i[0]) * (1 - fee)
                zaplatim_fee += float(i[1]) * float(i[0]) * fee
                summ -= float(i[1])
            else:
                prod += summ * float(i[0]) * (1 - fee)
                zaplatim_fee += summ * float(i[0]) * fee
                break
        return [prod, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте

class Bitfinex:
    def __init__(self, name, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.name = name
        self.fee = 0.002
        self.Withdrawal_fee = {'BTC': 0.0005, 'ZEC': 0.001, 'BCH': 0.0005, 'ETH': 0.01}

    def skolko_mojno_kypit(self, summ, order_book_bitfinex):  # Сумма в  валюте, Валютная пара
        kypit = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_bitfinex != 0:
            for i in order_book_bitfinex["asks"]:
                if (float(i['price']) * float(i['amount']) < summ):
                    kypit += float(i['amount']) * (1 - fee)
                    zaplatim_fee += float(i['amount']) * fee
                    summ -= float(i['price']) * float(i['amount'])
                else:
                    kypit += summ / float(i['price']) * (1 - fee)
                    zaplatim_fee += summ / float(i['price']) * fee
                    break
            return [kypit, zaplatim_fee, i['price']]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

    def na_skolko_mojno_prodat(self, summ, order_book_bitfinex):  # Сумма во  валюте, Валютная пара
        prod = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_bitfinex != 0:
            for i in order_book_bitfinex["bids"]:
                if (float(i['amount']) < summ):
                    prod += float(i['amount']) * float(i['price']) * (1 - fee)
                    zaplatim_fee += float(i['amount']) * float(i['price']) * fee
                    summ -= float(i['amount'])
                else:
                    prod += summ * float(i['price']) * (1 - fee)
                    zaplatim_fee += summ * float(i['price']) * fee
                    break
            return [prod, zaplatim_fee, i['price']]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

class Wex:
    def __init__(self, name, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.name = name
        self.fee = 0.002
        self.time_zone = 0
        self.Withdrawal_fee = {'BTC': 0.001, 'ZEC': 0.001, 'BCH': 0.001, 'ETH': 0.001, 'LTC': 0.001, 'DASH': 0.001, 'XRP': 0, 'DOGE': 0, 'XMR': 0}
        self.pairs_wex = 'bch_btc-zec_btc-eth_btc-ltc_btc'

    def call_api(self,method, **kwargs):
        #time.sleep(0.17)  # По правилам биржи нельзя больше 6 запросов в секунду
        payload = {'nonce': int(str(round(time.time() * 1000000))[2:-4:1])}
        if kwargs:
            payload.update(kwargs)
        payload['method'] = method

        payload = urllib.parse.urlencode(payload)

        H = hmac.new(self.API_SECRET.encode('utf-8'), payload.encode('utf-8'), hashlib.sha512)
        #print(payload.encode('utf-8'))
        sign = H.hexdigest()

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self.API_KEY,
                   "Sign": sign}

        conn = http.client.HTTPSConnection("wex.nz")
        conn.request("POST", "/tapi", payload, headers)
        response = conn.getresponse().read()
        conn.close()

        #Пропустить ошибку запроса
        try:
            obj = json.loads(response.decode('utf-8'))
        except:
            obj = {}
            pass
        obj.update({'Res': ''})
        try:
            if obj['error'] != '':
                obj.update({'Res':'False'})
        except KeyError:
            pass
        if obj['Res'] == '':
            obj.update({'Res': 'True'})
        return obj

    def balans(self):
        bal = self.call_api("getInfo")
        return bal

    def order_sell(self, summ,para,price):
        order = self.call_api("Trade", pair=para, type='sell', rate=price, amount=summ)
        return order
    def order_buy(self, summ,para,price):
        order = self.call_api("Trade", pair=para, type='buy', rate=price, amount=summ)
        return order

    def orderbook(self,para):
        try:
            #print(datetime.now(),'Пытаюсь получить книгу ордеров с Wex...')
            #time.sleep(0.35) # По правилам биржи нельзя больше 180 запросов в минуту
            r = requests.get('https://wex.nz/api/3/depth/' + para, timeout=0.6)
            return r.json()
            #print(datetime.now(), 'Книга получена с Wex, возвращаю:')
        except Exception:
            return 0
            pass

    def readorderbooks(self,market,para):
        try:
            ob = open((CURR_DIR + '/orderbooks/' + market + para + '.txt'), 'r')
            timestamp = float(ob.readline()) + 5.97
            if timestamp > round(time.time(), 2):
                data = json.loads(str(ob.readline()))
                ob.close()
            else:
                ob.close()
                return 0
        except ValueError as err:
            print('ValueError',err)
            return 0
        except FileNotFoundError as err:
            print('FileNotFoundError',err)
            return 0
        return data

    def cancelOrder(self, orderNumber):
        rezult = self.call_api('CancelOrder', order_id=orderNumber)
        return  rezult

    def returnOpenOrders(self):
        return self.call_api('ActiveOrders')

    def chek_and_close_open_orders(self,pair,order_book,account_name):
        ret = []
        try:
            open_orders = self.returnOpenOrders()['return']
            if order_book != 0 and open_orders != {}:
                # ОТменяем каждый висящий ордер
                for ord in open_orders: # ord - номер ордера, open_orders[ord] - инфо об ордере по данному номеру
                    if open_orders[ord]['pair'] == pair:
                        log_close_order('На ', self.name, 'Найден ордер: ', ord, open_orders[ord])
                        if open_orders[ord]['type'] == 'buy':  # Определяем тип ордера, отменяем и выставляем новый
                            if float(open_orders[ord]['rate']) < float(order_book['bids'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['bids'][0][0]) * 1.003, 4)
                                cancelorder = self.cancelOrder(ord)
                                neworder = self.order_buy(open_orders[ord]['amount'], open_orders[ord]['pair'], rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 больше чем в первом bids
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name': account_name, 'market': self.name, 'order_pair': pair,
                                          'order_type': open_orders[ord]['type'], 'amount': open_orders[ord]['amount'], 'old_price': open_orders[ord]['rate'],
                                          'old_summary_amount': (open_orders[ord]['amount'] * open_orders[ord]['rate']),
                                       'old_time_created': datetime.fromtimestamp(int(open_orders[ord]['timestamp_created'])).strftime('%Y-%m-%d %H:%M:%S'),
                                          'new_price': rate, 'new_summary_amount': (round((rate * open_orders[ord]['amount']), 8)),
                                          'new_time_created': str(datetime.now())[:str(datetime.now()).find('.')],
                                          'deprofit_summ': ((round((rate * open_orders[ord]['amount']), 8)) - round((open_orders[ord]['amount'] * open_orders[ord]['rate']),8)),
                                          'deprofit_procent': (round((((rate / float(open_orders[ord]['rate'])) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders', dic)
                                ret.append(round((((rate / float(open_orders[ord]['rate'])) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Спрос из кнги:', order_book['bids'][0][0])
                        elif open_orders[ord]['type'] == 'sell':
                            if float(open_orders[ord]['rate']) > float(order_book['asks'][0][0]):  # Проверяем что цена ордера не самая первая в стакане
                                rate = round(float(order_book['asks'][0][0]) / 1.003, 4)
                                cancelorder = self.cancelOrder(ord)
                                neworder = self.order_sell(open_orders[ord]['amount'], open_orders[ord]['pair'], rate)  # Выставляем новый ордер на сумму из отмененного ордера по цене на 0.00000007 меньше чем в первом asks
                                log_close_order('Результат отмены ордера: ', cancelorder, 'Результат создания ордера по курсу: ', rate, neworder)
                                dic = {'account_name': account_name, 'market': self.name, 'order_pair': pair,
                                          'order_type': open_orders[ord]['type'], 'amount': open_orders[ord]['amount'], 'old_price': open_orders[ord]['rate'],
                                          'old_summary_amount': (open_orders[ord]['amount'] * open_orders[ord]['rate']),
                                       'old_time_created': datetime.fromtimestamp(int(open_orders[ord]['timestamp_created'])).strftime('%Y-%m-%d %H:%M:%S'),
                                          'new_price': rate, 'new_summary_amount': (round((rate * open_orders[ord]['amount']), 8)),
                                          'new_time_created': str(datetime.now())[:str(datetime.now()).find('.')],
                                          'deprofit_summ': (round((open_orders[ord]['amount'] * open_orders[ord]['rate']),8) - (round((rate * open_orders[ord]['amount']), 8))),
                                          'deprofit_procent': (round((((float(open_orders[ord]['rate']) / rate) - 1) * 100), 3))}
                                log_close_order(dic)
                                bd.write('close_orders', dic)
                                ret.append(round((((float(open_orders[ord]['rate']) / rate) - 1) * 100), 3))
                            else:
                                log_close_order('Ордер самый верхний в стакане.', 'Предложение из кнги:', order_book['asks'][0][0])
                        else:
                            print('Не удалось определить тип ордера. Ничего не делаю')
                return ret
            else:
                log_close_order('Получить ордера на WEX НЕ УДАЛОСЬ!!!!!')
                log_close_order(order_book)
                log_close_order(open_orders)
                return 0
        except KeyError:
            print('Что то пошло не так или ордеров нет!')
            return 0
            pass

    def last_bid_ask(self,order_book):
        return {'bid':order_book['bids'][0][0],'ask':order_book['asks'][0][0]}

    def skolko_mojno_kypit(self, summ, order_book_wex):  # Сумма в ПЕРВОЙ валюте, order_book_poloniex от валютной пары
        kypit = 0
        fee = self.fee
        zaplatim_fee = 0
        if order_book_wex != 0:
            for i in order_book_wex["asks"]:
                if (float(i[0]) * float(i[1]) < summ):
                    kypit += float(i[1]) * (1 - fee)
                    zaplatim_fee += float(i[1]) * fee
                    summ -= float(i[0]) * float(i[1])
                else:
                    kypit += summ / float(i[0]) * (1 - fee)
                    zaplatim_fee += summ / float(i[0]) * fee
                    break
            return [kypit, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте
        else:
            return False

    def na_skolko_mojno_prodat(self, summ, order_book_wex):  # Сумма во ВТОРОЙ валюте, order_book_poloniex от валютной пары
        prod = 0
        fee = self.fee
        zaplatim_fee = 0
        for i in order_book_wex["bids"]:
            if (float(i[1]) < summ):
                prod += float(i[1]) * float(i[0]) * (1 - fee)
                zaplatim_fee += float(i[1]) * float(i[0]) * fee
                summ -= float(i[1])
            else:
                prod += summ * float(i[0]) * (1 - fee)
                zaplatim_fee += summ * float(i[0]) * fee
                break
        return [prod, zaplatim_fee, i[0]]  # Просто инфо о коммисии в покупаемой валюте


#_______________________
work_pairs = [{'Poloniex': 'BTC_ZEC', 'Exmo': 'ZEC_BTC', 'Bitfinex': 'zecbtc', 'Wex': 'zec_btc'},
              {'Poloniex': 'BTC_ETH', 'Exmo': 'ETH_BTC', 'Bitfinex': 'ethbtc', 'Wex': 'eth_btc'},
              {'Poloniex': 'BTC_XRP', 'Exmo': 'XRP_BTC', 'Bitfinex': 'xrpbtc', 'Wex': 'xrp_btc'},
              {'Poloniex': 'BTC_ETC', 'Exmo': 'ETC_BTC', 'Bitfinex': 'etcbtc', 'Wex': 'etc_btc'},
              {'Poloniex': 'USDT_ETC', 'Exmo': 'USDT_ETC', 'Bitfinex': 'USDT_ETC', 'Wex': 'USDT_ETC'},
              {'Poloniex': 'USDT_ZEC', 'Exmo': 'USDT_ETC', 'Bitfinex': 'USDT_ETC', 'Wex': 'USDT_ETC'},
              {'Poloniex': 'USDT_ETH', 'Exmo': 'USDT_ETC', 'Bitfinex': 'USDT_ETC', 'Wex': 'USDT_ETC'},
              {'Poloniex': 'USDT_BCH', 'Exmo': 'USDT_BCH', 'Bitfinex': 'USDT_BCH', 'Wex': 'USDT_BCH'},
              {'Poloniex': 'BTC_DASH', 'Exmo': 'DASH_BTC', 'Bitfinex': 'dashbtc', 'Wex': 'dash_btc'},
              {'Poloniex': 'BTC_XMR', 'Exmo': 'XMR_BTC', 'Bitfinex': 'xmrbtc', 'Wex': 'xmr_btc'},
              {'Poloniex': 'BTC_STR', 'Exmo': 'STR_BTC', 'Bitfinex': 'STRbtc', 'Wex': 'STR_btc'},
              {'Poloniex': 'BTC_XEM', 'Exmo': 'XEM_BTC', 'Bitfinex': 'XEMbtc', 'Wex': 'XEM_btc'},
              {'Poloniex': 'BTC_BCHABC', 'Exmo': '', 'Bitfinex': '', 'Wex': ''},
              {'Poloniex': 'BTC_BCHSV', 'Exmo': '', 'Bitfinex': '', 'Wex': ''},
              {'Poloniex': 'BTC_BCH', 'Exmo': 'BCH_BTC', 'Bitfinex': '', 'Wex': ''}
] #Пара polo, Exmo, Bit, Wex

Poloniex_blm = Poloniex(**configs['Poloniex_blm'])
Exmo_blm = Exmo(**configs['Exmo_blm'])
Bitfinex_blm = Bitfinex(**configs['Bitfinex_blm'])
Wex_blm = Wex(**configs['Wex_blm'])

Poloniex_Elka = Poloniex(**configs['Poloniex_Elka'])
Exmo_Elka = Exmo(**configs['Exmo_Elka'])
Bitfinex_Elka = Bitfinex(**configs['Bitfinex_Elka'])
Wex_Elka = Wex(**configs['Wex_Elka'])

Poloniex_dispell = Poloniex(**configs['Poloniex_dispell'])
Exmo_dispell = Exmo(**configs['Exmo_dispell'])

Poloniex_Andy_blm_shared = Poloniex(**configs['Poloniex_Andy_blm_shared'])
Exmo_Andy_blm_shared = Exmo(**configs['Exmo_Andy_blm_shared'])
