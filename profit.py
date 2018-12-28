#!/usr/bin/python3
import os
import time
import json
import requests
import sqlite3
import urllib.request, http.client
# эти модули нужны для генерации подписи API
import hmac, hashlib

from urllib.parse import urlparse
from datetime import datetime
import MarketClass

from MarketClass import bd
#MarketClass.bd.update('orders_greate_failed',{'set': {'amount':'3.263'},'where':{'account_name': 'blm', 'pair':'BTC_ZEC'}}) #dic = {'set': {'field': 'value', 'field': 'value', }, 'where': {'field': 'value', 'field': 'value', }}

# bd.delite('orders_greate_failed',{'account_name': 'blm','cur_time':'2018-02-08 02:02:17'})
# bd.write('orders_greate_failed',{'account_name': 'blm', 'pair':'BTC_BCH', 'market':'EXMO','ord_type': 'sell', 'price': '0.15116602', 'amount':'0.02006892','total_amount':str(0.15116602 * 0.02006892),'cur_time':'2018-02-10 09:23:24'})

# bd.update('balans_log',{'set': {'account_name': 'blm'}, 'where': {'account_name': 'dispell'}})
# bd.update('close_orders',{'set': {'account_name': 'blm'}, 'where': {'account_name': 'dispell'}})
# bd.update('trades',{'set': {'account_name': 'blm'}, 'where': {'account_name': 'dispell'}})#dic = {'set': {'field': 'value', 'field': 'value', }, 'where': {'field': 'value', 'field': 'value', }}


#Создаем лог файл______
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = CURR_DIR + '/logs/log_balans.txt'
def log(*args):
    l = open(LOG_FILE, 'a')
    print(datetime.now(), *args)
    print(datetime.now(), *args, file=l)
    l.close()
#_______________________
Poloniex = MarketClass.Poloniex_blm
Exmo = MarketClass.Exmo_blm
Wex = MarketClass.Wex_blm
def get_order_book_exmo():
    while True:
        try:
            r = requests.get('https://api.exmo.com/v1/order_book/?pair=' + "ZEC_BTC,ETH_BTC,ETH_LTC,ETC_BTC,LTC_BTC,XRP_BTC,XMR_BTC,BTC_USDT,ETH_USDT,DOGE_BTC,BTC_RUB,BCH_BTC", timeout=2)
            order_book_exmo = r.json()
            break
        except Exception as err:
            print(err)
            pass
    return order_book_exmo

order_book_exmo = get_order_book_exmo()

def denejnii_vid(sum):
    summ = str(sum)
    dlinna = len(summ)
    x = 0
    summ_f = ' '
    while x < dlinna:
        if x == 0:
            summ_f = ',' + summ[-3:]
            x += 3
        else:
            summ_f = ',' + summ[-(x + 3): -x] + summ_f
            x += 3
    return summ_f[1:]

def get_all_bal_in_btc_rub(tekyshii,order_book_exmo):
    BTC_stalo = float(tekyshii['Exmo']['BTC']) + float(tekyshii['Poloniex']['BTC']) + float(tekyshii['Wex']['BTC'])
    ZEC_stalo = float(tekyshii['Exmo']['ZEC']) + float(tekyshii['Poloniex']['ZEC']) + float(tekyshii['Wex']['ZEC'])
    BCH_stalo = float(tekyshii['Exmo']['BCH']) + float(tekyshii['Poloniex']['BCH']) + float(tekyshii['Wex']['BCH'])
    ETH_stalo = float(tekyshii['Exmo']['ETH']) + float(tekyshii['Poloniex']['ETH']) + float(tekyshii['Wex']['ETH'])
    XRP_stalo = float(tekyshii['Exmo']['XRP']) + float(tekyshii['Poloniex']['XRP']) + float(tekyshii['Wex']['XRP'])
    DOGE_stalo = round((float(tekyshii['Exmo']['DOGE']) + float(tekyshii['Poloniex']['DOGE'])), 8)
    now_bal = {'BTC': (BTC_stalo), 'ZEC': (ZEC_stalo), 'BCH': (BCH_stalo), 'ETH': (ETH_stalo), 'XRP': (XRP_stalo), 'DOGE': DOGE_stalo}
    for i in now_bal:
        if now_bal[i] != 0 and i != "BTC":
            # print (order_book_exmo[i + '_BTC']['ask'][0][0], pribil[i], pribil['BTC'])
            now_bal['BTC'] += float(order_book_exmo[i + '_BTC']['ask'][0][0]) * now_bal[i]
    now_bal_in_rub = round(now_bal['BTC'] * float(order_book_exmo['BTC_RUB']['ask'][0][0]))
    now_bal_in_rub = denejnii_vid(now_bal_in_rub)
    return [round(now_bal['BTC'],8), now_bal_in_rub]

#bilo:
bilo_23_11_17 = {
                'Exmo':{'BTC':0.18648995+0.02925, 'ZEC':0.60944052, 'BCH': 0, 'ETH': 0, 'XRP': 347.710605+30.5, 'DOGE': 0}, # 17/12/17 0.02925BTC купил маме и Диме 29.12.17 Купил димону 30.5 риплов на его 4тыс (ОТДАЛ)
                'Poloniex': {'BTC':0.03049607, 'ZEC':4.46960569 + 1.4, 'BCH': 0.82483493, 'ETH': 0.99980904, 'XRP': 0, 'DOGE': 13125.105}, #14/12/17 Добавил 1,4 ZEC с общего(ОТДАЛ)
                'Wex': {'BTC':0+0.105, 'ZEC':1.999, 'BCH': 0.25, 'ETH': 0, 'XRP': 0} #Добавил 16/12/17 0,105 BTC с общего счета на полониксе (ОТДАЛ)
                 }
# tekyshii = {'Exmo':{'BTC':0.1216687, 'ZEC':0.50189563, 'BCH': 0.31654413}, 'Poloniex': {'BTC':0.10228599, 'ZEC':4.45820093, 'BCH': 0.50829096}}
def get_now_balanses():
    tekyshii = {'Exmo':{'BTC':0, 'ZEC':0, 'BCH': 0, 'ETH': 0, 'XRP': 0, 'DOGE': 0}, 'Poloniex': {'BTC':0, 'ZEC':0, 'BCH': 0, 'ETH': 0, 'XRP': 0, 'DOGE': 0}, 'Wex': {'BTC':0, 'ZEC':0, 'BCH': 0, 'ETH': 0, 'XRP': 0}}

    bal_exmo = Exmo.call_api("user_info")
    bal_poloniex = Poloniex.call_api(command="returnAvailableAccountBalances")

    balans_wex = {}
    balans_wex_pr = Wex.balans()
    if balans_wex_pr['Res'] == 'False':
        log('Неудалось получить баланс с Wex.')
    else:
        for key in balans_wex_pr['return']['funds'].keys():
            balans_wex[str(key).upper()] = balans_wex_pr['return']['funds'][key]

    #print (bal_poloniex['exchange'])
    for i in bal_exmo['balances']:
        for b in bilo_23_11_17['Exmo']:
            if i == b:
                #print(tekyshii['Exmo'][b], bal_exmo['balances'][i])
                tekyshii['Exmo'][b] = bal_exmo['balances'][i]
    for i in bal_poloniex['exchange']:
        for b in bilo_23_11_17['Poloniex']:
            #print(i,b)
            if i == b:
                tekyshii['Poloniex'][b] = bal_poloniex['exchange'][i]

    for i in balans_wex:
        for b in bilo_23_11_17['Wex']:
            #print(i,b)
            if i == b:
                tekyshii['Wex'][b] = balans_wex[i]

    return tekyshii
#Посчитать суточную прибыль
def get_day_profit(tarade_limit,day):
    LOG_FILE_trade = CURR_DIR + '/logs/log_2.6.2_blm/' + str(day) + 'trades_log.txt'
    prof = 0
    try:
        ob = open(LOG_FILE_trade, 'r')
        for line in ob:
            if line.find('%') != -1:
                #print(line)
                #print(line[-7:-2])
                prof += round((tarade_limit / 100 * float(line[-9:-2])),8)
        ob.close()

    except ValueError as err:
        print('ValueError', err)
        return 0
    except FileNotFoundError as err:
        print('FileNotFoundError', err)
        return 0
    return round(prof,8)
#Конец подсчета
if __name__ == "__main__":
    tekyshii = get_now_balanses()

    BTC_bilo = bilo_23_11_17['Exmo']['BTC'] + bilo_23_11_17['Poloniex']['BTC'] + bilo_23_11_17['Wex']['BTC'] #- 0.11 #Вывод с полоникса
    ZEC_bilo = bilo_23_11_17['Exmo']['ZEC'] + bilo_23_11_17['Poloniex']['ZEC'] + bilo_23_11_17['Wex']['ZEC']
    BCH_bilo = bilo_23_11_17['Exmo']['BCH'] + bilo_23_11_17['Poloniex']['BCH'] + bilo_23_11_17['Wex']['BCH']
    ETH_bilo = bilo_23_11_17['Exmo']['ETH'] + bilo_23_11_17['Poloniex']['ETH'] + bilo_23_11_17['Wex']['ETH']
    XRP_bilo = bilo_23_11_17['Exmo']['XRP'] + bilo_23_11_17['Poloniex']['XRP'] + bilo_23_11_17['Wex']['XRP']
    DOGE_bilo = bilo_23_11_17['Exmo']['DOGE'] + bilo_23_11_17['Poloniex']['DOGE']

    BTC_stalo = round((float(tekyshii['Exmo']['BTC']) + float(tekyshii['Poloniex']['BTC']) + float(tekyshii['Wex']['BTC'])),8)
    ZEC_stalo = round((float(tekyshii['Exmo']['ZEC']) + float(tekyshii['Poloniex']['ZEC']) + float(tekyshii['Wex']['ZEC'])),8)
    BCH_stalo = round((float(tekyshii['Exmo']['BCH']) + float(tekyshii['Poloniex']['BCH']) + float(tekyshii['Wex']['BCH'])),8)
    ETH_stalo = round((float(tekyshii['Exmo']['ETH']) + float(tekyshii['Poloniex']['ETH']) + float(tekyshii['Wex']['ETH'])),8)
    XRP_stalo = round((float(tekyshii['Exmo']['XRP']) + float(tekyshii['Poloniex']['XRP']) + float(tekyshii['Wex']['XRP'])),8)
    DOGE_stalo = round((float(tekyshii['Exmo']['DOGE']) + float(tekyshii['Poloniex']['DOGE'])),8)

    BCH_bilo += 0 #18.12.17 17:31 Купили с Дюшей на общие
    BTC_bilo += -0.113+0.10531047-0.127 #18.12.17 17:31 Продали Битки с общего счета полониекс с Дюшей (ОТДАЛ)
    ZEC_bilo -= 2.3424 #prodl na $ общие с Дюшей (взаиморасчет см. гугл табл)

    BCH_bilo += 0.2 + 0.2149 #19.12.17 17:31 Купил на наторгованные ботом деньги + докупил bch по курсу 0.16150001 на 0,0347битка которые перетратил от Дюши когда 0,1бтс скидывал
    BTC_bilo += -0.03026000 #18.12.17 17:31 Продали Битки наторгованные ботом за 1,5 недели

    BCH_bilo += 0.06622517 #20.12.17 10:12 Купил на наторгованные ботом деньги  bch на 0,0138 битка по курсу 0.20899997
    BTC_bilo += -0.01384105 #20.12.17 10:12 Продали Битки наторгованные ботом за 1,5 недели

    BTC_bilo += -0.01000008 #25.12.17 10:12 Продали Битки наторгованные ботом за 1,5 недели купил 13158 DOGE rate 0.00000076

    BTC_bilo += -(0.00649953 + 0.00357974) #31.12.17 10:12 Продали Битки наторгованные ботом купил 71.89 XRP rate 0.00013999
    XRP_bilo += 71.89

    ZEC_bilo += 1.06 #01.01.2018 Ввел свои Зеки с майнинга

    ZEC_bilo += -2 #Продал общие с Дюшей 2 зека 08/01/2018 (взаиморасчет см. гугл табл)
    ZEC_bilo += -1 #Продал общие с Дюшей 1 зека 11/01/2018 (взаиморасчет см. гугл табл)
    XRP_bilo += 500 #Купили общие с Дюшей 500 риплов за баксы проданные с зеков 11/01/2018 (взаиморасчет см. гугл табл)
    ZEC_bilo += 1.5 #Ввел общие с Дюшей 1,5 зека с криптонатора 11/01/2018 НЕ ДОЛЖЕН
    BTC_bilo += (0.20434898 - 0.0008) #Ввел 0,2 битка Антона на Полоникс 11/01/2018

    BTC_bilo += -0.1325155 #13/01/18 купил на деньги Наташи себе 950 риплов по курсу 0.00013949 на 0,1325155 битка
    XRP_bilo += 950 #13/01/18 купил на деньги Наташи себе 950 риплов по курсу 0.00013949 на 0,1325155 битка

    XRP_bilo += 328.8 #Купили общие с Дюшей 328.8 риплов за баксы проданные с зеков 17/01/2018 по курсу 1,1$ на 350$ (взаиморасчет см. гугл табл)
    ZEC_bilo += 0.4259 #Купили общие с Дюшей 0.4259 зеки за баксы проданные с зеков 17/01/2018 по курсу 465$ на 200$ (взаиморасчет см. гугл табл)
    DOGE_bilo += 30033 #Купили общие с Дюшей 30500 Доги за баксы проданные с зеков 17/01/2018 по курсу 60 предварительно купив 0,0183 битка по курсу 11000$ на 200$ (взаиморасчет см. гугл табл)

    ZEC_bilo += 0.2648 #Ввел свои зеки с майнинга  18/01/18
    BTC_bilo -= 0.03 #24/01/18 Вывел битки наторгованные ботом по курсу 118700$ получил 355доларов или 19200р на карту
    BTC_bilo -= 0.00420820 #27/01/18 купил Димону Немов на эти деньги, можно считать вывел в рубли 3000р

    ZEC_bilo += 1.2  # Ввыел общие с Дюшей 1,2 зека с криптонатора  02/02/18 к себе НЕ ДОЛЖЕН

    BTC_bilo -= 0.02293436 #Димон перевел 10тыс руб на покупку РИплов 05/02/18 Продал свои -0.02293436 BTC (Димону перекинул 236 риплов)
    XRP_bilo += 236 # Димонены риплы на моем балансе (Димону перекинул 236 риплов)

    BTC_bilo -= 0.02925  # Перекинул Димону на его акк полоникс все битки купленные маме и ему в декабре 06/02/2018
    XRP_bilo -= (236 + 30.5)  # Перекинул Димону все его риплы на ексмо 06/02/2018
    ZEC_bilo -= 0.07  # Перекинул Димону все его риплы на ексмо 06/02/2018

    ZEC_bilo += 0.73  # Ввел свои намайненные 11/02/18
    ZEC_bilo -= 1  ##Продал 1 ZEC по курсу 0.05171701 BTC 11/02/18
    BTC_bilo += 0.05171701 ##Продал 1 ZEC по курсу 0.05171701 BTC 11/02/18
    ZEC_bilo -= 1  ##Продал 1 ZEC по курсу 0.05244002 BTC 11/02/18
    BTC_bilo += 0.05244002  ##Продал 1 ZEC по курсу 0.05244002 BTC 11/02/18

    ZEC_bilo += 0.47  #Ввел свои зеки 18/02/18
    ZEC_bilo += 0.4  # Ввел зеки с общего с Дюшей кошелька 18/02/18 НЕ ДОЛЖЕН
    ZEC_bilo += 0.1568565  # Ввел свои зеки которые месяц майнились у Петрухи 22/02/18

    BTC_bilo-=0.05 #Продал наторгованные за февраль по курсу 11340$ on 566#
    ZEC_bilo += 0.24  # Ввел свои зеки 06/03/18
    ZEC_bilo -= 6.29  # Вывел все что брал на общий с Дюшей 06/03/18
    BTC_bilo -= 0.7  # Вывел все что брал на общий с Дюшей 06/03/18
    DOGE_bilo -= 30100  # Вывел все что брал на общий с Дюшей 06/03/18
    XRP_bilo -= 829  # Вывел все что брал на общий с Дюшей 06/03/18

    #print(BTC_stalo, '_', tekyshii)
    pribil = {'BTC':round((BTC_stalo-BTC_bilo),8), 'ZEC':round((ZEC_stalo-ZEC_bilo),8), 'BCH':round((BCH_stalo-BCH_bilo),8), 'ETH':round((ETH_stalo-ETH_bilo),8), 'XRP':round((XRP_stalo-XRP_bilo),8), 'DOGE':round((DOGE_stalo-DOGE_bilo),8)}
    log('Грязная прибыль : ', pribil)
    log('Текущий баланс всех бирж: ', tekyshii)
    log('Текущий баланс всех бирж суммированный по парам. BTC: ', BTC_stalo, ' ZEC: ', ZEC_stalo, ' BCH: ', BCH_stalo, ' ETH: ', ETH_stalo, ' XRP: ', XRP_stalo, 'DOGE: ', round(DOGE_stalo,3))
    for i in pribil:
        if pribil[i] != 0 and i != "BTC":
           #print (order_book_exmo[i + '_BTC']['ask'][0][0], pribil[i], pribil['BTC'])
            pribil['BTC'] += float(order_book_exmo[i + '_BTC']['ask'][0][0]) * pribil[i]

    log('Прибыль BTC за вычетом неудачных торгов : ', round(pribil['BTC'],8), 'Что в рублях: ', round(pribil['BTC'] * float(order_book_exmo['BTC_RUB']['ask'][0][0])))
    now_in_btc = get_all_bal_in_btc_rub(tekyshii,order_book_exmo)
    log('Текущий баланс в BTC: ', now_in_btc[0], 'что в рублях: ', now_in_btc[1])


    now = datetime.now()
    month = int(now.month)
    if month < 10:
        month = '0' + str(month)
    day = int(now.day) - 1
    if day < 10:
        day = '0' + str(day)
    predday = str(now.year) + '-' + str(month) + '-' + str(day)  # Вчерашний день
    today = str(now)[0:str(now).find(' '):1]
    yesterday = predday
    print('за вчера заработано: ', get_day_profit(0.01,yesterday), ' BTC', 'Что в рублях: ', round(get_day_profit(0.01,yesterday) * float(order_book_exmo['BTC_RUB']['ask'][0][0])))
    print('за сегодня заработано: ', get_day_profit(0.01,today), ' BTC', 'Что в рублях: ', round(get_day_profit(0.01,today) * float(order_book_exmo['BTC_RUB']['ask'][0][0])))
    #print (BTC_stalo, '_', BTC_bilo, '_', ZEC_stalo, '_', ZEC_bilo, '_', BCH_stalo, '_', BCH_bilo)
    #print (BTC_stalo-BTC_bilo, ZEC_stalo-ZEC_bilo, BCH_stalo-BCH_bilo)
