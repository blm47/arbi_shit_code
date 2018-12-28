#!/usr/bin/python3
#! _*_ coding: UTF-8 _*_
#02/04/18 Добавлен прокси
#ver 3.0.1
import telebot
import MarketClass
import ofd
from datetime import datetime
from datetime import timedelta
from Telegram_procedyri import denejnii_vid
import requests
import json
import os
import pytesseract
from PIL import Image
import time
from telebot import apihelper

from ofd import *
import queue
import threading
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import subprocess
from configobj import ConfigObj



def run_in_threads(func, L, **kwargs):
    threads = []
    Q = queue.Queue()

    def dec(Q):
        def real_decor(fun):
            def new_f(*args, **kwargs):
                a = [*args][0]
                try:
                    r = fun(*args, **kwargs)
                except Exception as e:
                    r = e#','.join(e.args)
                Q.put({str(a):r})
            return new_f
        return real_decor

    for l in L:
        d = {**kwargs}
        t = threading.Thread(target=dec(Q)(func), args=(l,), kwargs=d)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    ans = {}
    while not Q.empty():
        ans.update(Q.get())
    return ans



def get_profit_reskript(d): #['2018-12-23T00:00:00', '2018-12-23T22:13:15']
    id_list = {x['id'] : x['name'] for x in test.get_OutletList()['records']}

    id_to_kkt_list = run_in_threads(test.get_KKTList, id_list.keys())
    id_to_kkt_list = {i : [x['fnFactoryNumber'] for x in v['records']] for i,v in id_to_kkt_list.items() if v['records'] != []}

    _ = []
    for y in id_to_kkt_list.values():
        for x in y:
            _.append(x)
    _ = run_in_threads(test.shift_list, _, begin=d[0], end=d[1])
    _ = {i: v['records'][0]['shiftNumber']  if v['records'] != [] else 0 for i,v in _.items()}
    _
    id_to_kkt_and_shift_list = {i : [{x:_[x]} for x in v] for i,v in id_to_kkt_list.items()}

    _ = []
    for x in id_to_kkt_and_shift_list.values():
        for y in x:
            if list(y.values())[0] > 0:
                _.append(y)
    _
    kkt_and_shift_list_to_profit = {i:{'cash' : v['shift']['income']['cash'], \
                                       'electronic': v['shift']['income']['electronic']} for i,v in \
                                    run_in_threads(test.shift_info, _).items()}

    id_to_profit = {}
    for k, x in id_to_kkt_and_shift_list.items():
        _ = {'cash': 0, 'electronic': 0}
        for i in x:
            try:
                _['cash'] +=kkt_and_shift_list_to_profit[str(i)]['cash'] // 100
                _['electronic'] +=kkt_and_shift_list_to_profit[str(i)]['electronic'] // 100
            except KeyError:
                pass
        id_to_profit.update({k:_})

    df = pd.DataFrame({y:v for x,y in id_list.items() for i,v in id_to_profit.items() \
                         if x==i}).T.sort_values(by=['electronic', 'cash'], ascending=False)

    df['total'] = df.sum(axis=1)
    df['cum_sum'] = df[::-1].total.cumsum()[::-1]
    df['profitability_in_%'] = (df.total / df.cum_sum[0]) * 100

    df['profitability_in_%'] = df['profitability_in_%'].map(lambda x: round(x,2))
    df.iloc[:,:-1] = df.iloc[:,:-1].applymap(lambda x: '{:0,} rub'.format(x))
    return df




configs = ConfigObj('configs.conf')
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
#_______
#tg://socks?server=ams1.proxy.veesecurity.com&port=443&user=PROXY_5AD9C373D4F18&pass=04dde631f5e3ebd7
#string = 'socks5://{userproxy}:{password}@{proxy_address}:{port}'.format(userproxy=userproxy,password=password,proxy_address=proxy_address,port=port)

string3 = configs['telega']['proxy']
#print(string)


import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
#_______
token = configs['telega']['token']
bot = telebot.TeleBot(token=token)
apihelper.proxy = {'https':string3,'http':string3}

#upd = bot.get_updates()

OutletList = []
OutletList_name = []
KKTList = []
KKTInfo = []
DocumentList = []
users = [326404173,235794451,323434566,446588133,444967002] # i'm, plan,elka,dimon,andy
bot_accounts = ['blm','Elka','dispell','Andy_blm_shared']



#last_upd = upd[-1]
#message_from_user = last_upd.message
#print(last_upd.message)

def get_profit(acc,date): #yyyy-mm-dd mojno yyyy-mm
    profit = 0
    deprofit = 0
    bd = MarketClass.DataBase('local', 'local.db')
    dic1 = {'account_name': acc,'sell_created': '{0}%'.format(date)}
    dic2 = {'account_name': acc, 'new_time_created': '{0}%'.format(date)}
    plus = bd.read('trades',dic1)
    minus = bd.read('close_orders',dic2)
    for i in plus:
        profit += i[12]
    for y in minus:
        deprofit += y[11]
    return {'profit': round(profit,8), 'deprofit':round(deprofit,8)}

def protorgovka(acc,date):
    #dic={'BTC_xrp':{'e_p':1,'p_e':1}}
    dic = {}
    bd = MarketClass.DataBase('local', 'local.db')
    dic1 = {'account_name': acc, 'sell_created': '{0}%'.format(date)}
    req=bd.read('trades',dic1)
    for x in req:
        if dic.get(x[1]) == None:
            dic.update({x[1]:{}})
            dic[x[1]].update({x[2]+'_'+x[3]:1})
        else:
            if dic[x[1]].get(x[2]+'_'+x[3]) == None:
                dic[x[1]].update({x[2] + '_' + x[3]: 1})
            else:
                dic[x[1]][x[2]+'_'+x[3]]+=1
    return dic

def losetrades(acc,date):
    #dic={'BTC_xrp':{'e_p':1,'p_e':1}}
    dic = {}
    bd = MarketClass.DataBase('local', 'local.db')
    dic1 = {'account_name': acc, 'curr_time': '{0}%'.format(date)}
    req=bd.read('logs_lose_trades',dic1)
    for x in req:
        if dic.get(x[1]) == None:
            dic.update({x[1]:{}})
            dic[x[1]].update({x[2]+'_'+x[7]:1})
        else:
            if dic[x[1]].get(x[2]+'_'+x[7]) == None:
                dic[x[1]].update({x[2] + '_' + x[7]: 1})
            else:
                dic[x[1]][x[2]+'_'+x[7]]+=1
    return dic



def get_order_book_exmo():
    try:
        f = open('order_book_exmo', 'r')
        order_book_exmo = f.readline()
        f.close()
        order_book_exmo = json.loads(order_book_exmo)
    except Exception:
        print("\n\n\n\n\nCan not read file order_book_exmo\n\n\n\n\n")
        try:
            r = requests.get(
                'https://api.exmo.com/v1/order_book/?pair=' + "ZEC_BTC,ETH_BTC,ETH_LTC,ETC_BTC,LTC_BTC,XRP_BTC,XMR_BTC,BTC_USDT,ETH_USDT,DOGE_BTC,BTC_RUB,BCH_BTC,DASH_BTC",
                timeout=3)
            order_book_exmo = r.json()
        except Exception as err:
            print(err)
            order_book_exmo = None
            pass
    return order_book_exmo

def get_all_balans(acc_name,time=str(datetime.now())[:10]): #yyyy-mm-dd hh:mm:ss
    err = ''
    order_book_exmo= get_order_book_exmo()
    bd = MarketClass.DataBase('local', 'local.db')
    try:
        all_balans = bd.read('balans_log',{'account_name':acc_name,'cur_time':'{0}%'.format(str(time)[:-4])})[-1][2]
    except IndexError:
        return [{},{},0,0,'\n <b>Не удалось получить баланс из базы, попробуйте позже</b>']
    all_balans = json.loads(all_balans.strip().replace("'", '"'))
    all_not_null_balans = {}
    all_not_null_balans_po_param = {}
    btc = 0
    for market in all_balans:
        all_not_null_balans.update({market:{}})
        for pair in all_balans[market]:
            if pair != 'Res':
                if float(all_balans[market][pair]) != 0:
                    try:
                        all_not_null_balans_po_param[pair] += float(all_balans[market][pair])
                    except KeyError:
                        for i in MarketClass.work_pairs:
                            if pair == i['Poloniex'][:3] or pair == i['Poloniex'][4:]:
                                all_not_null_balans_po_param.update({pair: 0})
                                all_not_null_balans_po_param[pair] += float(all_balans[market][pair])
                    all_not_null_balans[market].update({pair: float(all_balans[market][pair])})

    for crypt in all_not_null_balans_po_param:
        if crypt == 'BTC':
            btc += all_not_null_balans_po_param[crypt]
        else:
            try:
                btc +=  float(order_book_exmo[crypt + '_BTC']['ask'][0][0]) * all_not_null_balans_po_param[crypt]
            except KeyError:
                err+='\n<code>Не удалось посчитать сколько будет в BTC {0} {1}</code>'.format(all_not_null_balans_po_param[crypt],crypt)
    now_bal_in_rub = round(btc * float(order_book_exmo['BTC_RUB']['ask'][0][0]))
    now_bal_in_rub = denejnii_vid(now_bal_in_rub)
    return [all_not_null_balans,all_not_null_balans_po_param,round(btc,8),now_bal_in_rub,err]

def get_Virychka():
    try:
        ob = open(('Virychka_log.txt'), 'r')
        data = json.loads(str(ob.readline()))
        ob.close()
        return data
    except Exception:
        pass



#@bot.message_handler(content_types='text')


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True,False)
    user_markup.row('Узнать профит','Отчеты')
    user_markup.row('Настройки')
    bot.send_message(message.chat.id,'Выберите', reply_markup=user_markup)
    print(message)

@bot.message_handler(commands=['start2'])
def handle_start(message):
    if list(filter(lambda x: x == message.chat.id, users)) != []:
        user_markup = telebot.types.ReplyKeyboardMarkup(True,False)
        user_markup.row('Получить список точек','Отчеты_')
        bot.send_message(message.chat.id,'Выберите', reply_markup=user_markup)
        print(message)

@bot.callback_query_handler(func=lambda c: True)
def inline(c):
    if c.data:
        if c.data.find('баланс') != -1:
            bal = get_all_balans(c.data[6:])
            otvet = 'Баланс суммированный по биржам: '
            #for i in bal[1]:
                #otvet += "\n" + i + ' : ' + str(round(bal[1][i],8))
            for i in sorted(bal[1]):
                otvet += "\n" + i + ' : ' + '%.8f' %bal[1][i]
            otvet += "\n" + 'Текущий баланс в BTC: ' + str(bal[2]) + "\n" + 'Что в рублях на сегодня : ' + str(bal[3]) + str(bal[4])
            bot.edit_message_text(text=otvet, chat_id=c.message.chat.id, message_id=c.message.message_id, parse_mode='HTML')
        elif c.data.find('торги') != -1:
            acc = c.data[5:c.data.find('?')]
            date = c.data[c.data.find('?')+1:]
            prof = get_profit(acc,date)
            otvet = 'Чистый плюс: ' + str(prof['profit']) + "\nНеудачные торги: " + str(prof['deprofit']) + "\nИтог: " + str(round((prof['profit'] - prof['deprofit']),8)) + "\nЧто в руб по текущему курсу: " + str(round((prof['profit'] - prof['deprofit']) * float(get_order_book_exmo()['BTC_RUB']['ask'][0][0])))
            otvet2= """<b>bold</b>, <strong>bold</strong>
        <i>italic</i>, <em>italic</em>
        <a href="URL">inline URL</a>
        <code>inline fixed-width code</code>
        <pre>pre-formatted fixed-width code block</pre>"""
            print(otvet)
            bot.edit_message_text(text=otvet, chat_id=c.message.chat.id, message_id=c.message.message_id, parse_mode='HTML')
        elif c.data.find('по месяцам') != -1:
            months={1:'Январь',2:'Февраль',3:'Март',4:'Апрель',5:'Мая',6:'Июнь',7:'Июль',8:'Август',9:'Сентябрь',10:'Октябрь',11:'Ноябрь',12:'Декабрь',}
            acc = c.data[10:c.data.find('?')]
            date = c.data[c.data.find('?')+1:]
            final_otvet=''
            now_month=int(date[5:])
            for x in range(now_month):
                x+=1
                if x<10:
                    date=date[:-2]+'0'+str(x)
                    prof = get_profit(acc, date)
                    otvet = '<code>Чистый плюс: ' + str(prof['profit']) + "\nНеудачные торги: " + str(
                        prof['deprofit']) + "\nИтог: </code><b>" + str(
                        round((prof['profit'] - prof['deprofit']), 8)) + "</b><code>\nЧто в руб по текущему курсу: " + str(round(
                        (prof['profit'] - prof['deprofit']) * float(get_order_book_exmo()['BTC_RUB']['ask'][0][0])))+"</code>"
                    final_otvet+="""\n<strong>За {0}:</strong>\n""".format(months[x])+otvet
                else:
                    date = date[:-2] + str(x)
                    prof = get_profit(acc, date)
                    otvet = '<code>Чистый плюс: ' + str(prof['profit']) + "\nНеудачные торги: " + str(
                        prof['deprofit']) + "\nИтог: </code><b>" + str(
                        round((prof['profit'] - prof['deprofit']), 8)) + "</b><code>\nЧто в руб по текущему курсу: " + str(round(
                        (prof['profit'] - prof['deprofit']) * float(get_order_book_exmo()['BTC_RUB']['ask'][0][0])))+"</code>"
                    final_otvet += """\n<strong>За {0}:</strong>\n""".format(months[x]) + otvet
            bot.edit_message_text(text=final_otvet, chat_id=c.message.chat.id, message_id=c.message.message_id, parse_mode='HTML')
        elif c.data.find('проторговка') !=-1:
            acc = c.data[11:c.data.find('?')]
            date = c.data[c.data.find('?') + 1:]
            trades = protorgovka(acc,date)
            otvet=''
            for para in trades:
                otvet+='<strong>Пара {0}:</strong>\n'.format(para)
                for arbitr in trades[para]:
                    otvet+='<code>По направлению {0} совершено {1} сделок</code>\n'.format(arbitr,trades[para][arbitr])
            otvet+='\n<em>Первой идет биржа на которой была сделка покупки, вторая - на которой сделка продажи.\n</em>' \
                   '<i>К примеру: BTC_XRP-> Exmo_Poloniex означает что Риплы куплены были на Ексмо и проданы на Полониксе</i>'
            bot.edit_message_text(text=otvet, chat_id=c.message.chat.id, message_id=c.message.message_id, parse_mode='HTML')
        elif c.data.find('losetrades') !=-1:
            acc = c.data[10:c.data.find('?')]
            date = c.data[c.data.find('?') + 1:]
            otvet=''
            l_trades=losetrades(acc,date)
            for para in l_trades:
                otvet+='<strong>Пара {0}:</strong>\n'.format(para)
                for arbitr in l_trades[para]:
                    otvet+='<code>По направлению {0} УПУЩЕНО {1} сделок</code>\n'.format(arbitr,l_trades[para][arbitr])
            otvet += '\n<em>Первой идет биржа на которой не удалось совершить сделку покупки, вторая - на которой не удалось совершить сделку продажи.\n</em>' \
                     '<i>К примеру: BTC_XRP-> Exmo_Poloniex означает что Риплы не были куплены на Ексмо и не были проданы на Полониксе\n' \
                     'По причине что на Ексмо не было BTC на покупку или на Полониксе не было Риплов для продажи на момент времени когда бот хотел сторговать</i>'
            bot.edit_message_text(text=otvet, chat_id=c.message.chat.id, message_id=c.message.message_id, parse_mode='HTML')

@bot.message_handler(content_types=['text'])
def handle_start(message):
    global OutletList, OutletList_name, KKTList
    if list(filter(lambda x: x == message.chat.id, users)) != []:
        try:
            if message.text == 'Узнать профит':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                for i in bot_accounts:
                    user_markup.row(i)
                if message.chat.id==users[0]:
                    user_markup.row('Lasombra')
                user_markup.row('/start')
                bot.send_message(message.chat.id, 'Выберите аккаунт', reply_markup=user_markup)

            elif message.text == 'Отчеты':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Сводный по месяцам','Текущая проторговка')
                user_markup.row('Упущенные торги за сегодня')
                user_markup.row('/start')
                bot.send_message(message.chat.id, 'Укажите Отчет', reply_markup=user_markup)

            if message.text == 'Настройки':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                if message.chat.id==users[0]:
                    user_markup.row('Clear DB')
                    user_markup.row('/start')
                    bot.send_message(message.chat.id, 'Выберите функцию', reply_markup=user_markup)
                else:
                    user_markup.row('/start')
                    bot.send_message(message.chat.id, 'Вы не Админ! Ха-ха!', reply_markup=user_markup)

            if message.text == 'Clear DB' and message.chat.id==users[0]:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                MarketClass.bd.clear()
                user_markup.row('/start')
                bot.send_message(message.chat.id, '<b>BD cleared</b>', reply_markup=user_markup, parse_mode="HTML")



            elif message.text == 'Сводный по месяцам':
                keyboard = telebot.types.InlineKeyboardMarkup()
                for i in bot_accounts:
                    keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data='по месяцам'+str(i) + '?' + str(datetime.now())[:str(datetime.now()).find(' ')][:-3]))
                if message.chat.id==users[0]:
                    keyboard.add(telebot.types.InlineKeyboardButton(text='Lasombra',callback_data='по месяцам' + 'Lasombra' + '?' + str(datetime.now())[:str(datetime.now()).find(' ')][:-3]))
                bot.send_message(message.chat.id, 'Укажите аккаунт', reply_markup=keyboard)

            elif message.text == 'Текущая проторговка':
                keyboard = telebot.types.InlineKeyboardMarkup()
                for i in bot_accounts:
                    keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data='проторговка'+str(i) + '?' + str(datetime.now())[:str(datetime.now()).find(' ')]))
                if message.chat.id == users[0]:
                    keyboard.add(telebot.types.InlineKeyboardButton(text='Lasombra',callback_data='проторговка' + 'Lasombra' + '?' + str(datetime.now())[:str(datetime.now()).find(' ')]))
                bot.send_message(message.chat.id, 'Укажите аккаунт', reply_markup=keyboard)

            elif message.text == 'Упущенные торги за сегодня':
                keyboard = telebot.types.InlineKeyboardMarkup()
                for i in bot_accounts:
                    keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data='losetrades'+str(i) + '?' + str(datetime.now())[:str(datetime.now()).find(' ')]))
                if message.chat.id == users[0]:
                    keyboard.add(telebot.types.InlineKeyboardButton(text='Lasombra',callback_data='losetrades' + 'Lasombra' + '?' + str(datetime.now())[:str(datetime.now()).find(' ')]))
                bot.send_message(message.chat.id, 'Укажите аккаунт', reply_markup=keyboard)

            elif list(filter(lambda x: x == message.text, bot_accounts)) != []:
                keyboard = telebot.types.InlineKeyboardMarkup()
                prepare = [{'Сегодня': 'торги' + message.text + '?' +str(datetime.now())[:str(datetime.now()).find(' ')]},
                           {'Вчера': 'торги' + message.text + '?' + str((datetime.now() - timedelta(1)))[:str(datetime.now()).find(' ')]},
                           {'Позавчера': 'торги' + message.text + '?' + str((datetime.now() - timedelta(2)))[:str(datetime.now()).find(' ')]},
                           {'Текущий месяц': 'торги' + message.text + '?' + str(datetime.now())[:str(datetime.now()).find(' ')][:-3]},
                           {'Узнать баланс':'баланс' + message.text}]
                for x in prepare:
                    for i in x:
                        keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data=x[i]))
                bot.send_message(message.chat.id, 'Выберите вариант отчета', reply_markup=keyboard)

            elif message.text=='Lasombra':
                keyboard = telebot.types.InlineKeyboardMarkup()
                prepare = [{'Сегодня': 'торги' + message.text + '?' +str(datetime.now())[:str(datetime.now()).find(' ')]},
                           {'Вчера': 'торги' + message.text + '?' + str((datetime.now() - timedelta(1)))[:str(datetime.now()).find(' ')]},
                           {'Позавчера': 'торги' + message.text + '?' + str((datetime.now() - timedelta(2)))[:str(datetime.now()).find(' ')]},
                           {'Текущий месяц': 'торги' + message.text + '?' + str(datetime.now())[:str(datetime.now()).find(' ')][:-3]},
                           {'Узнать баланс':'баланс' + message.text}]
                for x in prepare:
                    for i in x:
                        keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data=x[i]))
                bot.send_message(message.chat.id, 'Выберите вариант отчета', reply_markup=keyboard)

            elif message.text == 'Получить список точек':
                OutletList_name.clear()
                OutletList.clear()
                r = ofd.test.call_api('OutletList',np='OK')
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                for i in r['records']:
                    OutletList_name.append(str(i['name']))
                    OutletList.append(i)
                    user_markup.row(str(i['name']))
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'Выберите Магазин', reply_markup=user_markup)
                #print(OutletList,OutletList_name)
            elif list(filter(lambda x: x == message.text, OutletList_name)) != []:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                KKTList.clear()
                for Outlet in OutletList:
                    #print(Outlet['name'])
                    if Outlet['name'] == str(message.text):
                        #print(Outlet)
                        r_KKTList = ofd.test.call_api('KKTList',id=Outlet['id'])
                        print(r_KKTList)
                        for KKT in r_KKTList['records']:
                            print(KKT)
                            KKTList.append(str(KKT['fnFactoryNumber']))
                            user_markup.row(str(KKT['fnFactoryNumber']))
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'Выберите Кассу', reply_markup=user_markup)
                print(KKTList)
                pass
            elif list(filter(lambda x: x == message.text, KKTList)) != []:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Выручка за вчера','Выручка за сегодня')
                r = ofd.test.call_api('KKTInfo',fn=message.text)
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'статус смены: {0}'.format(r['cashdesk']['shiftStatus']), reply_markup=user_markup)
                print(KKTList)
            elif message.text == 'Выручка за вчера':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Выручка за вчера','Выручка за сегодня')
                data = str(datetime.now() - timedelta(1))
                data = [[data[:data.find(' ')] + 'T09:00:00', data[:data.find(' ')] + 'T23:59:59'],
                        [str(datetime.now())[:data.find(' ')] + 'T09:00:00',
                         str(datetime.now())[:data.find(' ')] + 'T23:59:59']]
                r1 = ofd.test.call_api('ShiftList',fn=KKTList[0],begin=data[0][0], end=data[0][1])
                print(r1['records'])
                r2 = ofd.test.call_api('ShiftInfo',fn=KKTList[0],shift=r1['records'][0]['shiftNumber'])
                print(r2)
                r3=ofd.test.call_api('DocumentList',fn=KKTList[0],shift=r1['records'][0]['shiftNumber'])
                print(r3['records'])
                for doc in r3['records']:
                    if doc['documentType'] == '3':
                        r4 = ofd.test.call_api('DocumentURL',fn=KKTList[0],fd=doc['fdNumber'])
                        DocumentList.append({'sum': denejnii_vid(str(doc['sum'])[:-2]), 'cash': denejnii_vid(doc['cash']), 'electronic': doc['electronic'],'fdNumber': doc['fdNumber'],'url':r4['taxcomReceiptUrl']})
                        bot.send_message(message.chat.id, "Номер документа: {0}\nСумма документа: {1}\nСсылка на документ: {2}".format(doc['fdNumber'],denejnii_vid(str(doc['sum'])[:-2]),r4['taxcomReceiptUrl']))
                otvev = "Открыта: {0}\nЗакрыта: {1}\nКассир: {2}\nОбщая выручка: {3}\nНаличман: {4}\nБезналик: {5}".format(r2['shift']['openDateTime'],r2['shift']['closeDateTime'],r2['shift']['cashier'],denejnii_vid(str(r2['shift']['income']['total'])[:-2]),denejnii_vid(str(r2['shift']['income']['cash'])[:-2]),denejnii_vid(str(r2['shift']['income']['electronic'])[:-2]))
                print(otvev)
                user_markup.row('/start2')
                bot.send_message(message.chat.id, otvev, reply_markup=user_markup)
                print(KKTList)
            elif message.text == 'Выручка за сегодня':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Выручка за вчера','Выручка за сегодня')
                data = str(datetime.now() - timedelta(1))
                data = [[data[:data.find(' ')] + 'T09:00:00', data[:data.find(' ')] + 'T23:59:59'],
                        [str(datetime.now())[:data.find(' ')] + 'T09:00:00',
                         str(datetime.now())[:data.find(' ')] + 'T23:59:59']]
                r1 = ofd.test.call_api('ShiftList',fn=KKTList[0],begin=data[1][0], end=data[1][1])
                print(r1['records'])
                r2 = ofd.test.call_api('ShiftInfo',fn=KKTList[0],shift=r1['records'][0]['shiftNumber'])
                print(r2)
                r3 = ofd.test.call_api('DocumentList', fn=KKTList[0], shift=r1['records'][0]['shiftNumber'])
                print(r3['records'])
                for doc in r3['records']:
                    print(doc)
                    if doc['documentType'] == '3':
                        r4 = ofd.test.call_api('DocumentURL', fn=KKTList[0], fd=doc['fdNumber'])
                        a=denejnii_vid(str(doc['sum'])[:-2])
                        b=denejnii_vid(str(doc['cash'])[:-2])
                        c=denejnii_vid(str(doc['electronic'])[:-2])
                        d=doc['fdNumber']
                        f=r4['taxcomReceiptUrl']
                        DocumentList.append({'sum': a, 'cash': b, 'electronic': c,'fdNumber': d, 'url': f})
                        bot.send_message(message.chat.id,
                                         "Номер документа: {0}\nСумма документа: {1}\nСсылка на документ: {2}".format(
                                             doc['fdNumber'], a, f))
                otvev = "Открыта: {0}\nЗакрыта: {1}\nКассир: {2}\nОбщая выручка: {3}\nНаличман: {4}\nБезналик: {5}".format(r2['shift']['openDateTime'],r2['shift']['closeDateTime'],r2['shift']['cashier'],denejnii_vid(str(r2['shift']['income']['total'])[:-2]),denejnii_vid(str(r2['shift']['income']['cash'])[:-2]),denejnii_vid(str(r2['shift']['income']['electronic'])[:-2]))
                print(otvev)
                user_markup.row('/start2')
                bot.send_message(message.chat.id, otvev, reply_markup=user_markup)
                print(KKTList)

            #Тут Отчеты_
            elif message.text == 'Отчеты_':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Сводный за вчера','Сводный за сегодня')
                user_markup.row('Вчера Москва', 'Текущие Москва')
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'Выберите Отчет', reply_markup=user_markup)

            elif message.text == 'Сводный за сегодня':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                asd = get_Virychka()
                bot.send_message(message.chat.id,
                                 "Сумма торгов по всем точкам на ТЕКУЩИЙ МОМЕНТ:\n    Общая: {0}\n    Наличка: {1}\n    Безналичка: {2}".format(
                                     asd['segodnya'][0], asd['segodnya'][1], asd['segodnya'][2]))
                print(asd)
                user_markup.row('Сводный за вчера','Сводный за сегодня')
                user_markup.row('Вчера Москва', 'Текущие Москва')
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'Выберите Отчет', reply_markup=user_markup)
            elif message.text == 'Сводный за вчера':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                asd = get_Virychka()
                bot.send_message(message.chat.id,
                                 "Сумма торгов по всем точкам:\n    Общая: {0}\n    Наличка: {1}\n    Безналичка: {2}".format(
                                     asd['vchera'][0], asd['vchera'][1], asd['vchera'][2]))
                print(asd)
                user_markup.row('Сводный за вчера','Сводный за сегодня')
                user_markup.row('Вчера Москва', 'Текущие Москва')
                user_markup.row('/start2')
                bot.send_message(message.chat.id, 'Выберите Отчет', reply_markup=user_markup)

            elif message.text == 'Текущие Москва':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                keyboard = telebot.types.InlineKeyboardMarkup()
                tmp2 = 'today.png'
                # d_end = (datetime.now()).replace(microsecond=0).isoformat()
                # d_start = (datetime.today()).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                # d = [d_start, d_end]
                # try:
                #     df = get_profit_reskript(d)
                # except Exception as e:
                #     df = pd.DataFrame()
                #     bot.send_message(message.chat.id, 'Не удалось сформировать отчет', reply_markup=user_markup)
                # tmp = 'temp.html'
                # tmp2 = 'temp.png'
                # df.to_html(tmp)
                # if os.name == 'nt':
                #     coding = 'cp1251'
                # else:
                #     coding = 'utf8'
                # subprocess.call( 'wkhtmltoimage --encoding %s -f \
                #     png --width 0 %s %s'%(coding, tmp,tmp2), shell=True)
                doc = open(tmp2, 'rb')
                #bot.send_document(message.chat.id, doc)
                bot.send_photo(message.chat.id, doc)

            elif message.text == 'Вчера Москва':
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                keyboard = telebot.types.InlineKeyboardMarkup()
                tmp2 = 'vchera.png'
                # d_end = (datetime.now() - timedelta(hours=24)).replace(hour=23, minute=59, second=59,microsecond=0).isoformat()
                # d_start = (datetime.today() - timedelta(hours=24)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                # d = [d_start, d_end]
                # try:
                #     df = get_profit_reskript(d)
                # except Exception as e:
                #     df = pd.DataFrame()
                #     bot.send_message(message.chat.id, 'Не удалось сформировать отчет', reply_markup=user_markup)
                # tmp = 'temp.html'
                # tmp2 = 'temp.png'
                # df.to_html(tmp)
                # if os.name == 'nt':
                #     coding = 'cp1251'
                # else:
                #     coding = 'utf8'
                # subprocess.call( 'wkhtmltoimage --encoding %s -f \
                #     png --width 0 %s %s'%(coding, tmp,tmp2), shell=True)
                doc = open(tmp2, 'rb')
                #bot.send_document(message.chat.id, doc)
                bot.send_photo(message.chat.id, doc)


            print(message)
        except Exception as err:
            print('!!!!!ERROORR',err)
    else:
        bot.send_message(message.chat.id, 'Бот в разработке. Для доступа обратитесь к разработчику')
        print(message)

@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
        file=message.photo
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        #tessdata_dir_config = '--tessdata-dir "C:/Program Files (x86)/Tesseract-OCR/tessdata"'
        tessdata_dir_config = '--tessdata-dir "/usr/share/tesseract-ocr/tessdata"'
        src = CURR_DIR +  '/tmp/' + file_info.file_path
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        img1 = Image.open(src)
        text = pytesseract.image_to_string(img1,lang='eng',config=tessdata_dir_config)
        if text.find("\nA") != -1:
            a = text[text.find("\nA"):]
            a=a[a.find(' ')+1:]
            if a[:a.find("\n")].find(' ') != -1:
                otvet=a[:a.find(' ')]
            else:
                otvet = a[:a.find("\n")]
        else:
            otvet='Не распознал'
        keyboard = telebot.types.InlineKeyboardMarkup()
        prepare = [{'Да': '/start2'},
                   {'Нет': '/start2'}]
        for x in prepare:
            for i in x:
                keyboard.add(telebot.types.InlineKeyboardButton(text=i, callback_data=x[i]))
        bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, 'Распознан артикул:' +"\n" + str(otvet) + "\n" + 'верно? ', reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, e)

def start_polling():
    try:
        bot.polling(none_stop=True)
    except Exception as err:
        print(err)
        time.sleep(23)
        start_polling()


if __name__ == "__main__":
    start_polling()
# def get_profit(message):
#     if message.text == 'Узнать профит':
#         bot.send_message(message.chat.id, 'За какой день в текущем месяце?')

# def get_profit(message):
#     if message.text.find('за') != -1:
#         dic = {'account_name':'blm','sell_created':'2018-01-{}%'.format(message.text[2:4])}
#         #bot.send_message(message.chat.id,'Введите диапазон дат в формате: yyyy-mm-dd,yyyy-mm-dd')
#         aa = MarketClass.bd.read('trades', dic)
#         print(aa)
#         vrem = 0
#         for i in aa:
#             vrem += i[12]
#         bot.send_message(message.chat.id, round(vrem,8),'без учета неудачных торгов')
# #print(message_from_user)
