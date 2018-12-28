#!/usr/bin/python3
#! _*_ coding: UTF-8 _*_
#Будет искать выгоду без учета коммисий за транзакции вывода с биржы на биржу
#Торгует не большими суммами и предлагает выводить средства только в том случае когда сумарная прибыль перекроет коммисии на вывод
#08/12/17 Добавлена и протестирована поддержка 3х бирж
#18/12/17 Отключил запрос книги ордеров по Bitfinex
#21/12/2017 Книгу ордеров берет с файла
#06/01/2018 Добавил поддержку Рипла
#23/01/2018 Добавил вывод в БД
#13/04/18 Закоментил brake 4шт при создании ордеров Исправил ошибку curr -> cur_time при записи Потерянамана
#20/09/18 Исправил ошибку создания сфейленных ордеров (round(,4))
import os
import time
import random
import json
import requests
import sqlite3
import urllib.request, http.client
# эти модули нужны для генерации подписи API
import hmac, hashlib

from urllib.parse import urlparse
from datetime import datetime
import MarketClass
#Создаем классы бирж:
bd = MarketClass.bd
Poloniex = MarketClass.Poloniex_dispell
Exmo = MarketClass.Exmo_dispell
Bitfinex = MarketClass.Bitfinex_blm
Wex = MarketClass.Wex('Wex','asfasfasf','asfasfasf')
ver = 'log_2.6.2'
account = 'dispell'
Withdrawal_fee_count = 10000 #Ожидаемое кол-во сделок перед выводом
want_profit = 0.23 #Желаемый профит В Процентах
#Создаем лог файл______
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
def log(*args):
    global ver, account, CURR_DIR
    day = str(datetime.now())[0:str(datetime.now()).find(' '):1]
    LOG_FILE = CURR_DIR + '/logs/' + ver + '_' + str(account) + '/' + str(day) + '_log.txt'
    try:
        l = open(LOG_FILE, 'a')
        print(datetime.now(), *args)
        print(datetime.now(), *args, file=l)
        l.close()
    except Exception as oshibka:
        print('Ошибка при записи лога!', str(oshibka))
        pass

def logtorgov(*args):
    global ver, account, CURR_DIR
    log(*args)
    day = str(datetime.now())[0:str(datetime.now()).find(' '):1]
    LOG_FILE_trade = CURR_DIR + '/logs/' + ver + '_' + str(account) + '/' + str(day) + 'trades_log.txt'
    try:
        lt = open(LOG_FILE_trade, 'a')
        print(datetime.now(), *args)
        print(datetime.now(), *args, file=lt)
        lt.close()
    except Exception as oshibka:
        print('Ошибка при записи лога!', oshibka)
        pass

def cur_time():
    return str(datetime.now())[:str(datetime.now()).find('.')]


x = 0
work_pairs = [{'Poloniex': 'BTC_ZEC', 'Exmo': 'ZEC_BTC', 'Bitfinex': 'zecbtc', 'Wex': 'zec_btc'},
              {'Poloniex': 'BTC_ETH', 'Exmo': 'ETH_BTC', 'Bitfinex': 'ethbtc', 'Wex': 'eth_btc'},
              {'Poloniex': 'BTC_BCH', 'Exmo': 'BCH_BTC', 'Bitfinex': 'bchbtc', 'Wex': 'bch_btc'},
              {'Poloniex': 'BTC_XRP', 'Exmo': 'XRP_BTC', 'Bitfinex': 'xrpbtc', 'Wex': 'xrp_btc'},
              {'Poloniex': 'BTC_DOGE', 'Exmo': 'DOGE_BTC', 'Bitfinex': 'dogebtc', 'Wex': 'doge_btc'}] #Пара polo, Exmo, Bit, Wex

#Валюта, Баланс,  Коммисия на вывод с Polo, Exmo, Bitfinex, WEX
balans_formated = [['BTC', 0.003, 0.0001, 0.001], ['BCH', 0.1, 0.0001, 0.001], ['ZEC', 0.5, 0.001, 0.001], ['DASH', 0.4, 0.01, 0.01], ['ETH', 0.5, 0.005, 0.01], ['LTC', 2.5, 0.001, 0.01], ['XRP', 850, 0.15, 0.02],
                   ['XMR', 1.4, 0.05, 0.05], ['ETC', 10, 0.01, 0.01]]
birji = [Poloniex,Exmo]
#______________________________________________________


#Подготовка к работе создаем счетчики и переменные с которыми будем работать______________________
#Вводим переменные с которыми будем работать
count_zdelok = {} #{'Poloniex_Exmo': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0}, 'Poloniex_Bitfinex': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0},
count_zdelok_mnim = {} #{'Poloniex_Exmo': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0}, 'Poloniex_Bitfinex': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0},
count_zdelok_summ = {} #Суммарный за ссесию по всем направлениям
profit_for_round = {}#{'Poloniex_Exmo': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0}, 'Exmo_Poloniex': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0},
profit_for_round_mnim = {}#{'Poloniex_Exmo': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0}, 'Exmo_Poloniex': {'BTC_ZEC': 0, 'BTC_ETH': 0, 'BTC_BCH': 0},
napravleniya = []
timer_open_orders = {}
timer_not_placed_orders = {}
#__________________________________
for b in birji:
    for b2 in birji:
        if b.name != b2.name:
            napravleniya.append(b.name + '_' + b2.name)
            # for i in napravleniya:
            #     if i == b2.name + '_' + b.name:
            #         napravleniya.pop()

for i in work_pairs:
    timer_open_orders.update({i['Poloniex']:0})
    timer_not_placed_orders.update({i['Poloniex']:0})
    for b in napravleniya:
        #b_invert = b[(b.find('_') + 1)::1] + '_' + b[0:b.find('_'):1]
        if count_zdelok.get(b) == None:
            count_zdelok.update({b: {}})
        if count_zdelok_mnim.get(b) == None:
            count_zdelok_mnim.update({b: {}})
        if count_zdelok_summ.get(b) == None:
            count_zdelok_summ.update({b: {}})
        if profit_for_round.get(b) == None:
            profit_for_round.update({b: {}})
        if profit_for_round_mnim.get(b) == None:
            profit_for_round_mnim.update({b: {}})
        # if profit_for_round.get(b_invert) == None:
        #     profit_for_round.update({b_invert: {}})
        count_zdelok[b].update({i['Poloniex']: 0})
        count_zdelok_mnim[b].update({i['Poloniex']: 0})
        count_zdelok_summ[b].update({i['Poloniex']: 0})
        profit_for_round[b].update({i['Poloniex']: 0})
        profit_for_round_mnim[b].update({i['Poloniex']: 0})
        #profit_for_round[b_invert].update({i['Poloniex']: 0})

def statistic():
    vrem = {}
    for napr in napravleniya:
        vrem.update({napr: {}})
        for para in work_pairs:
            vrem[napr].update({para['Poloniex']: [count_zdelok_mnim[napr][para['Poloniex']], profit_for_round_mnim[napr][para['Poloniex']]]})
    return vrem


log('Зверь начал работать!')
#______________________________________________________________________
balans_checker = 0
timer_statistic = 0
while x < 1:
    time.sleep(0.21) #В целях экономия процессорного времени
#Добавил выведение статистики по упущеной прибыли______08/12/17
    if timer_statistic == 0 or timer_statistic < round(time.time()):
        stat = statistic()
        for key in stat:
            log('По направлению', key, ' :')
            for paraname in stat[key].keys():
                log('По паре ', paraname, ' можно было совершить ', stat[key][paraname][0],
                    ' сделок. Упущенная прибыль: ', stat[key][paraname][1])
        timer_statistic = round(time.time()) + 47*60
#окончание вывода статистики___________________________

        # _______Начало переписанного кода
    for para in work_pairs: #work_pairs = [{'Poloniex':'BTC_ZEC','Exmo':'ZEC_BTC','Bitfinex':'zecbtc'},
        # Обнуляем книги ордеров
        order_book_exmo = 0
        order_book_poloniex = 0
        order_book_bitfinex = 0
        order_book_wex = 0
# Получаем балансы: ___
        if balans_checker < 1:
            try:
                print('Получаем баланс с Ексмо:')
                balans_exmo = Exmo.call_api("user_info")
                if balans_exmo['Res'] == 'False':
                    print('Неудалось получить баланс с Ексмо. Возвращаюсь в начало')
                    continue
                balans_exmo = balans_exmo['balances']
                print('Баланс Exmo: ', balans_exmo)
                print('Получаем баланс с Полоникса:')
                balans_poloniex = Poloniex.call_api(command="returnBalances")
                while balans_poloniex['Res'] == 'False':
                    balans_poloniex = Poloniex.call_api(command="returnBalances")
                # balans_poloniex = call_api_poloniex(command="returnAvailableAccountBalances") #Получение ДОСТУПНОГО Баланса
                # balans_poloniex = balans_poloniex['exchange']
                print('Баланс Poloniex: ', balans_poloniex)
                print('Получаем баланс с Wex:')
                balans_wex = {}
                # balans_wex_pr = Wex.balans()
                # if balans_wex_pr['Res'] == 'False':
                #     print('Неудалось получить баланс с Wex. Возвращаюсь в начало')
                #     continue
                # else:
                #     for key in balans_wex_pr['return']['funds'].keys():
                #         balans_wex[str(key).upper()] = balans_wex_pr['return']['funds'][key]
                # print('Баланс Wex: ', balans_wex)
                balans_bitfinex = {}
                balanses = {Poloniex.name:balans_poloniex, Exmo.name: balans_exmo, Bitfinex.name:balans_bitfinex,Wex.name:balans_wex}
                # nowBTC =float(balanses['Exmo']['BTC']) + float(balanses['Poloniex']['BTC']) + float(balanses['Wex']['BTC'])
                # nowZEC =float(balanses['Exmo']['ZEC']) + float(balanses['Poloniex']['ZEC']) + float(balanses['Wex']['ZEC'])
                # nowBCH =float(balanses['Exmo']['BCH']) + float(balanses['Poloniex']['BCH']) + float(balanses['Wex']['BCH'])
                # nowETH =float(balanses['Exmo']['ETH']) + float(balanses['Poloniex']['ETH']) + float(balanses['Wex']['ETH'])
                log('Баланс на биржах: ', balanses)
                bd.write('balans_log',{'account_name': account, 'cur_time':cur_time(), 'all_balanses': balanses})
                # log('Текущий баланс всех бирж суммированный по парам. BTC: ', nowBTC, ' ZEC: ', nowZEC, ' BCH: ', nowBCH, ' ETH: ', nowETH)
                balans_checker += 1
            except Exception:
                pass
#Балансы получены________
#Получаем книги ордеров:_____
        #log('Получаем книгу ордеров с Ексмо по паре: ', para['Exmo'], '...')
        order_book_exmo = Exmo.readorderbooks(Exmo.name, para['Exmo'])
        #log('Книга ордеров с Exmo Получена')
        #log('Получаем книгу ордеров с Полоникса по паре: ', para['Poloniex'], '...')
        order_book_poloniex = Poloniex.readorderbooks(Poloniex.name, para['Poloniex'])
        #log('Книга ордеров с Полоникса получена')
        #log('Получаем книгу ордеров с Wex по паре: ', para['Wex'], '...')
        #order_book_wex = Wex.readorderbooks(Wex.name,para['Wex'])
        order_book = {'Poloniex': order_book_poloniex, 'Exmo': order_book_exmo, 'Wex': order_book_wex, 'Bitfinex': order_book_bitfinex}
        # for book in order_book:
        #     if order_book[book] != 0:
        #         log('Книга ордеров по ', book, 'Получена')
#Все книги ордеров по i-ой паре получены начинаем вычислять
        crypto_sell = para['Poloniex'][0:para['Poloniex'].find('_'):1]      #BTC - Валюта которую продаем
        crypto_buy = para['Poloniex'][(para['Poloniex'].find('_') + 1)::1]  #ZEC - Валюта которую покупаем
#Получаем сумму на которую будем торговать
        for bal in balans_formated:  # balans_formated = [['BTC', 0.02, 0.0001, 0.001], ['BCH', 0.1, 0.0001, 0.001], ['ZEC', 0.5, 0.001, 0.001],
            if bal[0] == crypto_sell:
                summ = bal[1]
                break
#Сумма получена
        for napravlenie in napravleniya:  # ['Poloniex_Exmo','Bitfeniex_Wex']
            birja1 = napravlenie[0:napravlenie.find('_'):1]  # Poloniex
            birja2 = napravlenie[(napravlenie.find('_') + 1)::1]  #Exmo
            for i in birji:
                if i.name == birja1:
                    birja1 = i
            for i in birji:
                if i.name == birja2:
                    birja2 = i
            if (birja1.skolko_mojno_kypit(summ, order_book[birja1.name]) != False) and (birja2.skolko_mojno_kypit(summ, order_book[birja2.name]) != False):
                trade1_2 = birja1.skolko_mojno_kypit(summ, order_book[birja1.name])
                trade2_1 = birja2.na_skolko_mojno_prodat(trade1_2[0] - (birja1.Withdrawal_fee[crypto_buy] / Withdrawal_fee_count), order_book[birja2.name])
                Pribil = trade2_1[0] - (birja2.Withdrawal_fee[crypto_sell] / Withdrawal_fee_count)
                procent_pribili = ((Pribil / summ) - 1) * 100
                if procent_pribili > want_profit:
                    log('На ', summ, ' ', crypto_sell, ' можно купить ', trade1_2[0], ' ',
                        crypto_buy, 'по курсу: ',trade1_2[2], ' на бирже ', birja1.name, '. И на них купить: ', trade2_1[0], ' ',
                        crypto_sell, 'по курсу: ',trade2_1[2], ' на ', birja2.name, '. Прибыль составит: ', (Pribil - summ), ' ',
                        crypto_sell, " или ", procent_pribili, "%", 'Кол-во сделок = ',
                        count_zdelok_summ[napravlenie][para['Poloniex']])
#Можно удачно сторговать!!! Записываем в переменные мнимую сделку счетчик и сумму в BTC____
                    count_zdelok_mnim[napravlenie][para['Poloniex']] += 1
                    profit_for_round_mnim[napravlenie][para['Poloniex']] += Pribil - summ
#Пытаемся сторговать:___
                    try:
                        log('текущий баланс на ', birja1.name, balanses[birja1.name][crypto_sell], crypto_sell, 'и на ',
                            birja2.name, balanses[birja2.name][crypto_buy], crypto_buy)
                        log(trade1_2[2],trade2_1[2])
                        if (float(balanses[birja1.name][crypto_sell]) > summ) and (float(balanses[birja2.name][crypto_buy]) > trade1_2[0]) and (float(trade1_2[2]) < float(trade2_1[2])):
                            balans_checker = 0
                            buysumm = round((trade1_2[0] / (1 - birja1.fee)),8)
                            logtorgov('OrderBook on ', birja1.name, ':', order_book[birja1.name])
                            logtorgov('OrderBook on ', birja2.name, ':', order_book[birja2.name])
                            logtorgov('Создаю ордер на ', birja1.name, 'по паре: ', para[birja1.name],  ' на покупку ', buysumm, ' ', crypto_buy, ' по курсу: ', trade1_2[2])
                            order_buy = birja1.order_buy(buysumm,para[birja1.name],trade1_2[2])
                            logtorgov('Ответ сервера: ', order_buy)
                            if order_buy['Res'] == 'True':
                                logtorgov('Ордер на покупку создан успешно.', 'Создаю ордер на ', birja2.name, 'по паре: ', para[birja2.name],  ' на продажу ', round(trade1_2[0],8), ' ', crypto_buy, ' по курсу: ', trade2_1[2])
                                order_sell = birja2.order_sell(round(trade1_2[0],8), para[birja2.name],trade2_1[2])
                                logtorgov('Ответ сервера: ', order_sell)
                                if order_sell['Res'] == 'True':
                                    logtorgov('Ордер на продажу был успешно создан')
                                    count_zdelok_summ[napravlenie][para['Poloniex']] += 1
                                    profit_for_round[napravlenie][para['Poloniex']] += Pribil - summ
                                    logtorgov('Успешно созданы оба ордера: ', '. Прибыль должна составить: ', round((Pribil - summ), 8), ' ', crypto_sell, " или  ", round(procent_pribili, 3), "%")
                                    bd.write('trades',{'account_name':account,'order_pair':para['Poloniex'],'buy_market':birja1.name,'sell_market':birja2.name,'buy_amount':buysumm,'buy_price':trade1_2[2],
                                                       'buy_summary_amount':summ,'buy_created':cur_time(),'sell_amount':trade1_2[0],'sell_price':trade2_1[2],'sell_summary_amount':trade2_1[0],
                                                       'sell_created':cur_time(),'profit_summ':round((trade2_1[0] - summ),8),'profit_procent':(round(procent_pribili, 3))})
                                    #break
                                elif order_sell['Res'] == 'False':
                                    logtorgov('Создать ордер на продажу на ', birja2.name, ' не удалось!!! Внимание!! Создаю заного')
                                    order_sell = birja2.order_sell(round(trade1_2[0], 8), para[birja2.name], trade2_1[2])
                                    logtorgov('Ответ сервера: ', order_sell)
                                    if order_sell['Res'] == 'False':
                                        logtorgov('Создать ордер на продажу на ', birja2.name,' не удалось повторно!!! Внимание!! Потерянамана!!!')
                                        bd.write('orders_greate_failed',{'account_name':account,'pair':para['Poloniex'],'market':birja2.name,'ord_type':'sell','price':trade2_1[2],'amount':round(trade1_2[0],8),
                                                                         'total_amount':trade2_1[0],'cur_time':cur_time()})
                                        #break
                            else:
                                logtorgov('Создать ордер на покупку на ', birja1.name, ' не удалось. на продажу не создаем')
                        else:
                            dic_write = {'account_name': account, 'pair': para['Poloniex'], 'market1': birja1.name,
                                                          'price1': trade1_2[2], 'amount1': trade1_2[0],
                                                          'total_amount1': summ,
                                                          'cur_bal1': balanses[birja1.name][crypto_sell],
                                                          'market2': birja2.name, 'price2': trade2_1[2],
                                                          'total_amount2': trade2_1[0],
                                                          'cur_bal2': balanses[birja2.name][crypto_buy],
                                                          'curr_time': cur_time(),
                                                          'lose_profit_summ': round((Pribil - summ), 8)}
                            dic_check = {'account_name': account, 'pair': para['Poloniex'], 'market1': birja1.name,
                                         'market2': birja2.name,
                                         'curr_time': (cur_time()[:-1] +'%')}
                            check = bd.read('logs_lose_trades',dic_check)
                            if check == []:
                                bd.write('logs_lose_trades', dic_write)
                            del dic_write
                            del dic_check
                            log('баланса не хватает для торгов!')
                    except KeyError:
                        log('не удалось получить доступ к балансу на ', birja1.name, ' и ', birja2.name)
                        pass
                else:
# Тут будет код проверки не исполненного ордера
                    try:
                        if timer_open_orders[para['Poloniex']] == 0 or timer_open_orders[para['Poloniex']] < round(time.time()):
                            log('Проверяю открытые ордера: ')
                            for i in birji:
                                oo = i.chek_and_close_open_orders(para[i.name],order_book[i.name],account)
                                log(oo)
                                if oo != 0:
                                    for proc in oo:
                                        logtorgov('Был пересоздан ордер на ', i.name, '. Прибыль: ', -proc, "%")
                            timer_open_orders[para['Poloniex']] = round(time.time()) + 60*random.randint(42,57)
                            balans_checker = 0
                            log('Закончил проверку открытых ордеров')
                    except Exception as err:
                        logtorgov('ОШИБКАМАНАМА!!! при проверки открытых ордеров: ', err)
# Тут конец этого кода
#Код проверки не созданных ордеров
                    try:
                        if timer_not_placed_orders[para['Poloniex']] == 0 or timer_not_placed_orders[para['Poloniex']] < round(time.time()):
                            log('Проверяю не созданные ордера в БД по паре: ', para['Poloniex'])
                            npo = bd.read('orders_greate_failed', {'account_name': account, 'pair': para['Poloniex']})
                            log(npo)
                            for i in birji:
                                log('Проверяю биржу: ', i.name)
                                if order_book[i.name] != 0 and balanses[i.name] != {}:
                                    for ord in npo:
                                        log(ord[3], round((float(ord[4]) / 1.02), 4),float(i.last_bid_ask(order_book[i.name])['bid']), float(ord[6]),float(balanses[i.name][crypto_sell]))
                                        log(ord[3], round((float(ord[4]) / 0.98), 4),float(i.last_bid_ask(order_book[i.name])['ask']), float(ord[5]),float(balanses[i.name][crypto_buy]))
                                        if ord[3] == 'buy' and round((float(ord[4]) / 1.02),4) > float(i.last_bid_ask(order_book[i.name])['bid']) and (float(ord[6]) < float(balanses[i.name][crypto_sell])):
                                            #создаем ордер удаляем запись из БД
                                            order = i.order_buy(round((float(ord[5]) / (1 - i.fee)),8),para[i.name],round((float(ord[4]) / 1.02),8))
                                            logtorgov('Создал сфейленный ордер на покупку по паре ', para[i.name], ' на бирже ', i.name, 'суммы в ', ord[5], ' по курсу ', round((float(ord[4]) / 1.02),8),
                                                      'результат: ', order)
                                            if order['Res'] == 'True':
                                                logtorgov('Ордер создан успешно. Удаляю запись из БД, прерываю проверку для обновления балансов')
                                                bd.delite('orders_greate_failed',{'cur_time':ord[7],'account_name':account,'pair':ord[1], 'amount':ord[5]})
                                                balans_checker = 0
                                                #break
                                        elif (ord[3] == 'sell' and round((float(ord[4]) / 0.98),4) < float(i.last_bid_ask(order_book[i.name])['ask']) and float(ord[5]) < float(balanses[i.name][crypto_buy])) :
                                            # создаем ордер удаляем запись из БД
                                            order = i.order_sell(round((float(ord[5]) / (1 - i.fee)),8),para[i.name],round((float(ord[4]) / 0.98),8))
                                            logtorgov('Создал сфейленный ордер на продажу по паре ', para[i.name], ' на бирже ', i.name, 'суммы в ', ord[5], ' по курсу ', round((float(ord[4]) / 0.98),8),'результат: ', order)
                                            if order['Res'] == 'True':
                                                logtorgov('Ордер создан успешно. Удаляю запись из БД, прерываю проверку для обновления балансов')
                                                bd.delite('orders_greate_failed',{'cur_time': ord[7], 'account_name': account, 'pair': ord[1],'amount': ord[5]})
                                                balans_checker = 0
                                                #break

                            log('Закончил проверку не созданных ордерох в БД')
                            timer_not_placed_orders[para['Poloniex']] = round(time.time()) + random.randint(42,197)
                    except Exception as err:
                        logtorgov('ОШИБКАМАНАМА!!! при проверке не созданных ордеровна по паре ', para['Poloniex'], err)
#Конец кода
                    print(datetime.now(), 'Не торгуем! Убыток при попытке сторговать ', para['Poloniex'], ' по направлению: ', napravlenie, ' = ', summ - Pribil, ' ', crypto_sell,
                         'Кол-во успешных сделок за сессию:', count_zdelok_summ[napravlenie][para['Poloniex']],
                        '~ Профит суммарный по данной паре и направлению: ', profit_for_round[napravlenie][para['Poloniex']])





        #________Конец переписанного кода



