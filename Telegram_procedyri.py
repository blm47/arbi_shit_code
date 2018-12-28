#!/usr/bin/python3
#! _*_ coding: UTF-8 _*_
import ofd
from datetime import datetime
from datetime import timedelta
from profit import denejnii_vid
import time
import json
import requests

from Telegram import *

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

timer_segodnya = 0
timer_vchera = 0
timer_getobexmo = 0
def log_Virychka(data):
    LOG_Virychka = 'Virychka_log.txt'
    try:
        l = open(LOG_Virychka, 'w')
        l.write(json.dumps(data))
        l.close()
    except Exception as oshibka:
        print('Ошибка при записи лога!', str(oshibka))
        pass

def return_Virychka():
    return Virychka

def get_all_virychka(data): #['2018-02-01T09:24:00','2018-02-01T23:59:00']
    ALL_SUMM = []
    obshii = 0
    nal = 0
    beznal = 0
    r = ofd.test.call_api('OutletList')
    for Outlet in r['records']:
        r2 = ofd.test.call_api('KKTList', id=Outlet['id'])
        for KKT in r2['records']:
            r3 = ofd.test.call_api('ShiftList', fn=KKT['fnFactoryNumber'], begin=data[0], end=data[1])
            for i in r3['records']:
                print(i)
                r4 = ofd.test.call_api('ShiftInfo', fn=KKT['fnFactoryNumber'], shift=i['shiftNumber'])
                print(r4)
                ALL_SUMM.append(
                    {'total': str(r4['shift']['income']['total'])[:-2], 'cash': str(r4['shift']['income']['cash'])[:-2],
                     'electronic': str(r4['shift']['income']['electronic'])[:-2]})
    print(ALL_SUMM)

    for i in ALL_SUMM:
        print(i)
        if i['total'] != '':
            obshii += int(i['total'])
        if i['cash'] != '':
            nal += int(i['cash'])
        if i['electronic'] != '':
            beznal += int(i['electronic'])
    return [denejnii_vid(obshii), denejnii_vid(nal), denejnii_vid(beznal)]

def get_order_book_exmo_global():
    while True:
        try:
            r = requests.get('https://api.exmo.com/v1/order_book/?pair=' + "ZEC_BTC,ETH_BTC,ETH_LTC,ETC_BTC,LTC_BTC,XRP_BTC,XMR_BTC,BTC_USDT,ETH_USDT,DOGE_BTC,BTC_RUB,BCH_BTC,DASH_BTC", timeout=2)
            order_book_exmo = r.json()
            break
        except Exception as err:
            print(err)
            order_book_exmo = None
            pass
    if order_book_exmo != None:
        try:
            f = open('order_book_exmo', 'w')
            f.write(json.dumps(order_book_exmo))
            f.close()
        except Exception:
            pass

Virychka = {'vchera': 0, 'segodnya': 0}
if __name__ == "__main__":

    while True:
        time.sleep(60)
        print('!!!!!!!!!!!!Цикл пошел!!!!')

#_________________________________________
        d_end = (datetime.now()).replace(microsecond=0).isoformat()
        d_start = (datetime.today()).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        d = [d_start, d_end]
        try:
            df = get_profit_reskript(d)
        except Exception as e:
            df = pd.DataFrame()
            #bot.send_message(message.chat.id, 'Не удалось сформировать отчет', reply_markup=user_markup)
        tmp = 'temp.html'
        tmp2 = 'today.png'
        df.to_html(tmp)
        if os.name == 'nt':
            coding = 'cp1251'
        else:
            coding = 'utf8'
        subprocess.call( 'wkhtmltoimage --encoding %s -f \
            png --width 0 %s %s'%(coding, tmp,tmp2), shell=True) 

#______________________________
        d_end = (datetime.now() - timedelta(hours=24)).replace(hour=23, minute=59, second=59,microsecond=0).isoformat()
        d_start = (datetime.today() - timedelta(hours=24)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        d = [d_start, d_end]
        try:
            df = get_profit_reskript(d)
        except Exception as e:
            df = pd.DataFrame()
            #bot.send_message(message.chat.id, 'Не удалось сформировать отчет', reply_markup=user_markup)
        tmp = 'temp.html'
        tmp2 = 'vchera.png'
        df.to_html(tmp)
        if os.name == 'nt':
            coding = 'cp1251'
        else:
            coding = 'utf8'
        subprocess.call( 'wkhtmltoimage --encoding %s -f \
            png --width 0 %s %s'%(coding, tmp,tmp2), shell=True) 
#______________________________________


        try:
            if timer_segodnya == 0 or timer_segodnya < int(time.time()):
                data = str(datetime.now() - timedelta(1))
                data = [[data[:data.find(' ')] + 'T09:00:00', data[:data.find(' ')] + 'T23:59:59'],
                        [str(datetime.now())[:data.find(' ')] + 'T09:00:00',
                         str(datetime.now())[:data.find(' ')] + 'T23:59:59']]
                Virychka['segodnya'] = get_all_virychka(data[1])

                timer_segodnya = int(time.time()) + 5 * 60
                print('timer_segodnya', timer_segodnya)

            if timer_vchera == 0 or timer_vchera < int(time.time()):
                data = str(datetime.now() - timedelta(1))
                data = [[data[:data.find(' ')] + 'T09:00:00', data[:data.find(' ')] + 'T23:59:59'],
                        [str(datetime.now())[:data.find(' ')] + 'T09:00:00',
                         str(datetime.now())[:data.find(' ')] + 'T23:59:59']]
                Virychka['vchera'] = get_all_virychka(data[0])
                timer_vchera = int(time.time()) + 60 * 60 * 5
                print('timer_vchera', timer_vchera)
            print('!!!!Virychka',Virychka)
            log_Virychka(Virychka)

            if timer_getobexmo == 0 or timer_getobexmo < int(time.time()):
                get_order_book_exmo_global()
                timer_getobexmo = int(time.time()) + 60 * 60



        except Exception as err:
            print('ERROR!!!!',err)
