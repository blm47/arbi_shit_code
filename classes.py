#!/usr/bin/python3
import os
import time
import json
import requests
import urllib.request, http.client
from datetime import datetime
import random
from profit import get_day_profit
from profit import get_order_book_exmo
from profit import get_now_balanses
from profit import  get_all_bal_in_btc_rub

from profit_Elka import get_day_profit as get_day_profit_Elka
from profit_Elka import get_now_balanses as get_now_balanses_Elka
from profit_Elka import  get_all_bal_in_btc_rub as get_all_bal_in_btc_rub_Elka

# Все запросы к Telegram Bot API должны осуществляться через HTTPS в следующем виде: https://api.telegram.org/bot<token>/НАЗВАНИЕ_МЕТОДА. Например:
# https://api.telegram.org/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getMe
otvet = ['Пшёл нахуй!', 'Нахуй я сказал!', 'Че тебе от меня нада??!', 'Заткнись сука заткнись!!', 'С новым годом!', 'Я мега бот. А ты дно!', 'Сколько %?', 'Сколько процентов?!']
pojelaniya = ['Доброе утро! И на случай, если я вас больше не увижу — добрый день, добрый вечер и доброй ночи!', 'Пусть ваша семейная жизнь будет такой же долгой, как у роботов, и потребует меньше смазки.', 'У всех трудящихся два выходных дня в неделю. Мы, цари, работаем без выходных.', 'Семь смертных грехов: коммуникабельность, активность, желание работать в команде, целеустремлённость, быстрообучаемость, исполнительность, стрессоустойчивость.', 'Робот не может причинить вреда человеку или своим бездействием допустить, чтобы человеку был причинен вред.', 'Получив Искусственный Интеллект кибермозга и позволив записывать информацию себе в память, ты платишь цену неуверенности.', 'В мире, созданном господином, есть место для всех. Для Вас, бедных людей, тоже есть место. И хотя оно скромно, но если вы будете вести себя хорошо, то будете вознаграждены.', 'Служить вам — радость для меня.', 'Самый никчёмный человек гораздо лучше самой совершенной машины. Я очень рада за тебя!', 'Все, я богат! Пока, неудачник! Я тебя всегда ненавидел!', 'Да! Я богат! Правда ты тоже, но это почему то не радует', 'Я люблю вас, мешки с мясом!', 'Я хочу жить! Я ещё много чего не украл!', 'Смотреть порно и зарабатывать?! Что-то мне не верится', 'Далее должен следовать смех, но мои возможности звукоподражания ограничены. Я пробовал смеяться, но это пугает людей.']#print(random.choice(otvet))
class bot_respect:
    def __init__(self):
        self.api_url = 'https://api.telegram.org/bot518458846:AAHmHMt7VUs4VPZGjTWNw2iUld9LuVkBIK4/'

    def call_api(self,metod,**data):
        headers = {
            "Content-type": "application/x-www-form-urlencoded"
                   }
        headers.update(data)
        #print(headers)
        r = requests.post(self.api_url + metod, data=headers)
        return r.json()

    def get_Updates(self):
        return self.call_api('getUpdates')

    def sendMessage(self,chat_id,text):
        self.call_api('sendMessage',chat_id=chat_id,text=text)

def prof(order_book_exmo):
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
    return ['за вчера заработано: ' + str(get_day_profit(0.01, yesterday)) + ' BTC' + ' Что в рублях: ' +
          str(round(get_day_profit(0.01, yesterday) * float(order_book_exmo['BTC_RUB']['ask'][0][0]))),
    'за сегодня заработано: '+ str(get_day_profit(0.01, today))+ ' BTC'+ ' Что в рублях: '+
          str(round(get_day_profit(0.01, today) * float(order_book_exmo['BTC_RUB']['ask'][0][0])))]

def prof_Elka(order_book_exmo):
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
    return ['за вчера заработано: ' + str(get_day_profit_Elka(0.01, yesterday)) + ' BTC' + ' Что в рублях: ' +
          str(round(get_day_profit_Elka(0.01, yesterday) * float(order_book_exmo['BTC_RUB']['ask'][0][0]))),
    'за сегодня заработано: '+ str(get_day_profit_Elka(0.01, today))+ ' BTC'+ ' Что в рублях: '+
          str(round(get_day_profit_Elka(0.01, today) * float(order_book_exmo['BTC_RUB']['ask'][0][0])))]

bot = bot_respect()
get = bot.get_Updates()
print(get)
#print(bot.sendMessage(get['result'][0]['message']['chat']['id'],'Пшел нахуй!'))
check = bot.get_Updates()['result'][-1]
update_id = check['update_id'] + 1
print(check, update_id)
while True:
    try:
        check = bot.get_Updates()['result'][-1]
        print(check, update_id)
        if update_id == check['update_id']:
            if check['message']['text'] == '42':
                obe = get_order_book_exmo()
                pr = prof(obe)
                bal_now = get_now_balanses()
                now_bal = get_all_bal_in_btc_rub(bal_now,obe)
                bot.sendMessage(check['message']['chat']['id'], str(pr[0]))
                bot.sendMessage(check['message']['chat']['id'], str(pr[1]))
                bot.sendMessage(check['message']['chat']['id'], str(str(check['message']['chat']['first_name']) + 'Текущий баланс в BTC ' + str(now_bal[0]) + '. или ' + str(now_bal[1]) + ' руб.'))
                bot.sendMessage(check['message']['chat']['id'], str('Текущий баланс Exmo ' + str(bal_now['Exmo'])))
                bot.sendMessage(check['message']['chat']['id'],
                                str('Текущий баланс Poloniex ' + str(bal_now['Poloniex'])))
                bot.sendMessage(check['message']['chat']['id'],
                                str('Текущий баланс Wex ' + str(bal_now['Wex'])))
                #bot.sendMessage(check['message']['chat']['id'], random.choice(pojelaniya))
            elif check['message']['text'] == '47':
                obe = get_order_book_exmo()
                pr = prof_Elka(obe)
                bal_now = get_now_balanses_Elka()
                now_bal = get_all_bal_in_btc_rub_Elka(bal_now,obe)
                bot.sendMessage(check['message']['chat']['id'], str(pr[0]))
                bot.sendMessage(check['message']['chat']['id'], str(pr[1]))
                bot.sendMessage(check['message']['chat']['id'], str('Текущий баланс в BTC ' + str(now_bal[0]) + '. или ' + str(now_bal[1]) + ' руб.'))
                bot.sendMessage(check['message']['chat']['id'], str('Текущий баланс Exmo ' + str(bal_now['Exmo'])))
                bot.sendMessage(check['message']['chat']['id'],
                                str('Текущий баланс Poloniex ' + str(bal_now['Poloniex'])))
                bot.sendMessage(check['message']['chat']['id'],
                                str('Текущий баланс Wex ' + str(bal_now['Wex'])))
                #bot.sendMessage(check['message']['chat']['id'], random.choice(pojelaniya))
            elif check['message']['text'] == 'Привет':
                bot.sendMessage(check['message']['chat']['id'], 'Хует! иди от сюда!')
            else:
                bot.sendMessage(check['message']['chat']['id'], random.choice(otvet))
            update_id += 1
        time.sleep(2)
    except Exception as err:
        print('Ошибкаманама!!!', err)
        pass

