#!/usr/bin/python3
import os
import copy
import random
import requests
import time
import numpy as np
import talib
from threading import Thread
from matplotlib.finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime as datetime
import json
from keras.models import model_from_json
from keras.optimizers import Nadam

import telebot
from telebot import apihelper

string3 = 'https://mike007:R7i7YbE@217.147.168.71:65233'
apihelper.proxy = {'https': string3, 'http': string3}

token = '601724826:AAF6GIYBjk9gSRf1T3Zd8tp4iU-Nsp0UdXY'
chat_id = [-1001270504939]#,-1001328391895] # -1001270504939, - Поднял бабла
bot = telebot.TeleBot(token)

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.name == 'posix':
    slesh = '/'
elif os.name == 'nt':
    slesh = "\\"
filename2 = CURR_DIR + slesh +'prj_files' + slesh + 'Pair_tBTCUSD_candles_timeframe_1D_fields_733.csv'  # minutes
filename3 = CURR_DIR +  slesh + 'prj_files' + slesh + 'Pair_tBTCUSD_candles_timeframe_1D_fields_733.csv'  # Days
f_m = open(filename2)
candles_minutes = f_m.readline()
f_m.close()
candles_minutes = json.loads(candles_minutes)

f_D = open(filename3)
candles_days = f_D.readline()
f_D.close()
candles_days = json.loads(candles_days)

generator = {
    '1': ['Вангую', "Пацаны", "Ребятушки", "Мужики", "Хомяки", "Нигеры", "Хей Салаги", "Вычисления показывают что",
          'Good news everyone'],
    'down1': ["Рынок сыпеться", "Крипте пизда", "Нависли тучи над Мордером"],
    "down2": ["Распродаемся", "Сливаемся", "Не шлангуем, продаем"],
    'up1': ["Биток ракета", "Стартуем", "Летим вверх"],
    'up2': ["Закупаемся", "Берем кредит и закупаемся", "Затариваемся", 'Покупаем']}
# generator = {
#     '1': [''],
#     'down1': [""],
#     "down2": [""],
#     'up1': [""],
#     'up2': [""]}


def load_model():
    # Загружаем данные об архитектуре сети из файла json
    json_file = open(CURR_DIR + slesh + "prj_files" + slesh + "Nigga_model.json", "r")
    loaded_model_json = json_file.read()
    json_file.close()
    # Создаем модель на основе загруженных данных
    loaded_model = model_from_json(loaded_model_json)
    # Загружаем веса в модель
    loaded_model.load_weights(CURR_DIR + slesh + "prj_files" + slesh + "Nigga_model.h5")
    # Компилируем модель
    opt = Nadam(lr=0.001)
    loaded_model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=['accuracy'])
    return loaded_model


def load_model2():
    # Загружаем данные об архитектуре сети из файла json
    json_file = open(CURR_DIR + slesh + "prj_files" + slesh + "Nigga2_model.json", "r")
    loaded_model_json = json_file.read()
    json_file.close()
    # Создаем модель на основе загруженных данных
    loaded_model = model_from_json(loaded_model_json)
    # Загружаем веса в модель
    loaded_model.load_weights(CURR_DIR + slesh + "prj_files" + slesh + "Nigga2_model.h5")
    # Компилируем модель
    opt = Nadam(lr=0.001)
    loaded_model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=['accuracy'])
    return loaded_model


class Strategy():
    def __init__(self):
        self.model = load_model()
        self.model2 = load_model2()

    def _RSI(self, candles):
        try:
            # fastk, fastd = talib.STOCHRSI(candles['close'], timeperiod=14, fastk_period=14, fastd_period=3,
            #                               fastd_matype=3)
            fastk, fastd = talib.STOCHRSI(candles['close'], timeperiod=14, fastk_period=14, fastd_period=3,
                                          fastd_matype=3)
            return fastd
        except Exception as err:
            print(err)
            return np.zeros(len(candles))

    def _MACD(self, candles):
        try:
            macd, macdsignal, macdhist = talib.MACD(candles['close'], fastperiod=12, slowperiod=26, signalperiod=9)
            return macdhist
        except Exception as err:
            print(err)
            return np.zeros(len(candles))

    def _DEMA(self, candles):
        try:
            # return np.zeros(len(candles))
            return talib.EMA(candles['close'], timeperiod=9)
        except Exception as err:
            print(err)
            return np.zeros(len(candles))

    def _SAR(self, candles):
        try:
            return talib.SAR(candles['high'], candles['low'], acceleration=0.02, maximum=0.2)
        except Exception as err:
            print(err)
            return np.zeros(len(candles))

    def _RsiMA(self, candles):
        try:
            RSI = talib.RSI(candles['close'], 14)
            RSI = list(np.nan_to_num(RSI))
            RSI = np.array(RSI)

            RsiMa = talib.EMA(RSI, 5)
            RsiMa = np.nan_to_num(RsiMa)
            return RsiMa
        except Exception as err:
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! EMA 12-5   | 11% on 19 trades
            # !!!!!ema 9
            print(err)
            return np.zeros(len(candles))

    def _QQE_NIK(self, candles, RSI_Period=14, SF=5, QQE_=4.236):

        close = candles['close']

        import talib

        Wilders_Period = RSI_Period * 2 - 1

        rsi = talib.RSI(close, RSI_Period)
        RsiMa = talib.EMA(rsi, SF)

        AtrRsi = [RsiMa[0]]

        for r in range(1, len(RsiMa)):
            AtrRsi.append(abs(RsiMa[r - 1] - RsiMa[r]))

        AtrRsi = np.array(AtrRsi)

        MaAtrRsi = talib.EMA(AtrRsi, Wilders_Period)
        dar = talib.EMA(MaAtrRsi, Wilders_Period) * QQE_

        DeltaFastAtrRsi = dar
        RSIndex = RsiMa

        newshortband, newlongband = [], []

        for r in range(len(RSIndex)):
            newshortband.append(RSIndex[r] + DeltaFastAtrRsi[r])
            newlongband.append(RSIndex[r] - DeltaFastAtrRsi[r])

        longband, shortband = np.zeros_like(newlongband), np.zeros_like(newlongband)

        for r in range(1, len(RSIndex)):
            if RSIndex[r - 1] > longband[r - 1] and RSIndex[r] > longband[r - 1]:
                longband[r] = max(longband[r - 1], newlongband[r])
            else:
                longband[r] = newlongband[r]

        for r in range(1, len(RSIndex)):
            if RSIndex[r - 1] < shortband[r - 1] and RSIndex[r] < shortband[r - 1]:
                shortband[r] = min(shortband[r - 1], newshortband[r])
            else:
                shortband[r] = newshortband[r]

        FastAtrRsiTL = []
        trend = 0

        for i in range(1, len(RSIndex)):
            if (RsiMa[i] >= shortband[i - 1]):
                trend = 1
            elif (RsiMa[i] <= longband[i - 1]):
                trend = -1

            if trend == 1:
                FastAtrRsiTL.append(longband[i])
            elif trend == -1:
                # print(i)
                FastAtrRsiTL.append(shortband[i])
        # print(len(np.array(FastAtrRsiTL)),len(np.array(RsiMa)))
        FastAtrRsiTL = np.array(FastAtrRsiTL)
        RsiMa = np.array(RsiMa)
        while len(FastAtrRsiTL) < len(RsiMa):
            FastAtrRsiTL = np.insert(FastAtrRsiTL, 0, np.zeros(1))
        return FastAtrRsiTL, RsiMa

    def nn_signal(self, candles, day_candles, shag=42):

        # macd = talib.RSI(candles['close'], 14)
        macd = self._RSI(candles)
        if day_candles != None:
            rsi_day = self._RSI(day_candles)
            # FastAtrRsiTL, RsiMa = self._QQE_NIK(day_candles)
        else:
            rsi_day = [i for i in range(42)]
            # FastAtrRsiTL, RsiMa = [random.randint(0,10)] , [random.randint(0,10)]
        v = []
        v.append(macd[-shag:])
        row_predict = self.model.predict(np.array(v))
        nnpredict = np.argmax(row_predict)
        predict_power = np.max(row_predict)
        v2 = []
        v2.append(rsi_day[-shag:])
        row_predict2 = self.model.predict(np.array(v2))
        nnpredict2 = np.argmax(row_predict2)
        predict_power2 = np.max(row_predict2)

        predict = []

        if nnpredict == 2 and predict_power > 0.4 and -1 < macd[-1] < 20 and rsi_day[-1] <= 90:  # and nnpredict2 != 0 :
            predict.append(1)
        elif nnpredict == 0 and predict_power > 0.4 and 101 > macd[-1] > 80 and rsi_day[-1] >= 10:  # and nnpredict2 != 2:
            predict.append(-1)

        if sum(predict) > 0:
            return 'long'
        elif sum(predict) < 0:
            return 'short'

    def nn_signal_test(self, candles, day_candles, shag=42):
        v = []
        RSI = talib.RSI(candles['close'], 14)
        macd = self._RSI(candles)
        if day_candles != None:
            rsi_day = self._RSI(day_candles)
        else:
            rsi_day = [50]
        v.append(macd[-shag:])
        row_predict = self.model.predict(np.array(v))
        nnpredict = np.argmax(row_predict)
        predict_power = np.max(row_predict)
        r = random.randint(0, 85) / 100

        predict = []

        if nnpredict == 2 and predict_power > 0 and macd[-1] < 20 and rsi_day[-1] < 90 and 70 > RSI[-1] > 30:
            predict.append(1)
        elif nnpredict == 0 and predict_power > 0 and macd[-1] > 80 and rsi_day[-1] > 10 and 70 > RSI[-1] > 30:
            predict.append(-1)

        if sum(predict) > 0:
            return 'long'
        elif sum(predict) < 0:
            return 'short'

    def nn_signal2(self, candles, shag=42):
        v = []
        rsi = self._RSI(candles)

        v.append(rsi[-shag:])
        row_predict = self.model2.predict(np.array(v))
        nnpredict = np.argmax(row_predict)
        predict_power = np.max(row_predict)
        r = random.randint(0, 85) / 100

        if (nnpredict == 2 and predict_power > 0 and rsi[-1] < 80) or (rsi[-2] > 101 and rsi[-1] > 101 and rsi[-3] > 101):  # or rsi[-3] < rsi[-2] < rsi[-1]:
            return 'close_short'
        elif (nnpredict == 0 and predict_power > 0 and rsi[-1] > 20) or (rsi[-2] < -1 and rsi[-1] < -1  and rsi[-3] < -1):  # or rsi[-3] > rsi[-2] > rsi[-1]:
            return 'close_long'

        if (rsi[-2] > 20 and rsi[-1] < 20): #(rsi[-1] + 3 < rsi[-2] and rsi[-1] < -1) or
            return 'close_long'
        elif (rsi[-2] < 80 and rsi[-1] > 80): #(rsi[-1] - 3 > rsi[-2] and rsi[-1] > 101) or
            return 'close_short'

    def nn_signal2_test(self, candles, shag=42):
        v = []
        rsi = self._RSI(candles)
        RSI = talib.RSI(candles['close'], 14)
        v.append(rsi[-shag:])
        row_predict = self.model2.predict(np.array(v))
        nnpredict = np.argmax(row_predict)
        predict_power = np.max(row_predict)
        r = random.randint(0, 100) / 100

        if (nnpredict == 2 and predict_power > 0.4 and rsi[-1] < 80) or (
                    rsi[-3] > 101 and rsi[-2] > 101 and rsi[-1] > 101):  # or rsi[-3] < rsi[-2] < rsi[-1]:
            return 'close_short'
        elif (nnpredict == 0 and predict_power > 0.4 and rsi[-1] > 20) or (
                    rsi[-3] < -1 and rsi[-2] < -1 and rsi[-1] < -1):  # or rsi[-3] > rsi[-2] > rsi[-1]:
            return 'close_long'

        if (rsi[-2] > 20 and rsi[-2] < 20) or RSI[-1] > 70:
            return 'close_short'
        elif (rsi[-2] < 80 and rsi[-2] > 80) or RSI[-1] < 30:
            return 'close_long'

    def signal(self, candles):
        rsi = self._RSI(candles)
        # macd = self._MACD(candles)
        # dema = self._DEMA(candles)
        # sar = self._SAR(candles)
        # rsima = self._RsiMA(candles)
        # FastAtrRsiTL, RsiMa = self._QQE_NIK(candles)
        predict = []

        # if rsima[-2] < 50 and rsima[-1] > 50:
        #     predict.append(1)
        # elif rsima[-2] > 50 and rsima[-1] < 50:
        #     predict.append(-1)

        # if macd[-2] < 0 and macd[-1] > 0  and ((rsi[-2] < 50 and rsi[-1] > 50) or (rsi[-3] < 50 and rsi[-2] > 50)):
        #    predict.append(1)
        # elif macd[-2] > 0 and macd[-1] < 0 and ((rsi[-2] > 50 and rsi[-1] < 50) or (rsi[-3] > 50 and rsi[-2] < 50)):
        #    predict.append(-1)
        # elif rsi[-2] < 50 and rsi[-1] > 50 and ((macd[-2] < 0 and macd[-1] > 0) or (macd[-3] < 0 and macd[-2] > 0)):
        #    predict.append(1)
        # elif rsi[-2] > 50 and rsi[-1] < 50 and ((macd[-2] > 0 and macd[-1] < 0) or (macd[-3] > 0 and macd[-2] < 0)):
        #    predict.append(-1)

        # if FastAtrRsiTL[-1] < RsiMa[-1]:
        #     predict.append(1)
        # elif FastAtrRsiTL[-1] > RsiMa[-1]:
        #     predict.append(-1)

        # if macd[-2] < 0 and macd[-1] > 0:
        #     predict.append(-1)
        # elif macd[-2] > 0 and macd[-1] < 0:
        #     predict.append(1)
        if rsi[-2] < 20 and rsi[-1] > 20:
            predict.append(1)
        elif rsi[-2] > 80 and rsi[-1] < 80:
            predict.append(-1)
        # if sar[-2] > candles['high'][-2] and sar[-1] < candles['low'][-1]:
        #     predict.append(1)
        # elif sar[-2] < candles['low'][-2] and sar[-1] > candles['high'][-1]:
        #     predict.append(-1)
        # if candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] < candles['close'][-1]:
        #     predict.append(1)
        # elif candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] > candles['close'][-1]:
        #     predict.append(-1)

        if sum(predict) > 0:
            return 'long'
        elif sum(predict) < 0:
            return 'short'

    def signal2(self, candles, day_candles):
        rsi_d = self._RSI(day_candles)
        macd = self._MACD(candles)
        macd_d = self._MACD(day_candles)
        dema = self._DEMA(candles)
        rsima = self._RsiMA(candles)
        rsima_d = self._RsiMA(day_candles)
        FastAtrRsiTL, RsiMa = self._QQE_NIK(day_candles)
        predict = []

        # if rsima_d[-2] < 50 and rsima_d[-1] > 50:# and (macd[-2] < 0 and macd[-1] > 0): #  macd_d[-1] > 0 and rsi_d[-1] > 60 and FastAtrRsiTL[-1] < RsiMa[-1] and
        #     predict.append(1)
        # elif rsima_d[-2] > 50 and rsima_d[-1] < 50:# and (macd[-2] > 0 and macd[-1] < 0): #  macd_d[-1] < 0 and rsi_d[-1] < 40 and FastAtrRsiTL[-1] > RsiMa[-1] and
        #     predict.append(-1)

        # if macd_d[-1] > 30 and (macd[-2] < 0 and macd[-1] > 0): #  macd_d[-1] > 0 and rsi_d[-1] > 60 and FastAtrRsiTL[-1] < RsiMa[-1] and
        #     predict.append(1)
        # elif macd_d[-1] < -30 and (macd[-2] > 0 and macd[-1] < 0): #  macd_d[-1] < 0 and rsi_d[-1] < 40 and FastAtrRsiTL[-1] > RsiMa[-1] and
        #     predict.append(-1)

        # ________________Work
        if rsi_d[-2] > rsi_d[-1] > 60 and (macd[-2] < 0 and macd[-1] > 0):
            predict.append(1)
        elif rsi_d[-2] < rsi_d[-1] < 40 and (macd[-2] > 0 and macd[-1] < 0):
            predict.append(-1)

        # if rsi_d[-3] > 60 and rsi_d[-2] > 60 and  rsi_d[-1] > 60 and (macd[-2] > 0 and macd[-1] < 0):
        #    predict.append(1)
        # elif rsi_d[-3] < 40 and rsi_d[-2] < 40 and  rsi_d[-1] < 40 and (macd[-2] < 0 and macd[-1] > 0):
        #    predict.append(-1)

        # if 50 < rsima[-2] < rsima[-1]:
        #    predict.append(1)
        # elif 50 > rsima[-2] > rsima[-1]:
        #    predict.append(-1)

        # if FastAtrRsiTL[-1] < RsiMa[-1]:
        #     predict.append(1)
        # elif FastAtrRsiTL[-1] > RsiMa[-1]:
        #     predict.append(-1)


        # if rsi[-2] < 50 and rsi[-1] > 50:
        #     predict.append(1)
        # elif rsi[-2] > 50 and rsi[-1] < 50:
        #     predict.append(-1)
        # if sar[-2] > candles['high'][-2] and sar[-1] < candles['low'][-1]:
        #     predict.append(1)
        # elif sar[-2] < candles['low'][-2] and sar[-1] > candles['high'][-1]:
        #     predict.append(-1)
        # if candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] < candles['close'][-1]:
        #     predict.append(1)
        # elif candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] > candles['close'][-1]:
        #     predict.append(-1)

        if sum(predict) > 0:
            return 'long'
        elif sum(predict) < 0:
            return 'short'

    def signal3(self, tf, min_candles):

        rsima_m = self._RsiMA(min_candles)
        # print(rsima_m)
        rsima = rsima_m[(tf // 60) - 1::(tf // 60) - 1]
        # print(rsima)
        # print(len(rsima_m), len(rsima))
        predict = []

        if rsima[-2] < 50 and rsima[-1] > 50:
            predict.append(1)
        elif rsima[-2] > 50 and rsima[-1] < 50:
            predict.append(-1)

        if sum(predict) > 0:
            return 'long'
        elif sum(predict) < 0:
            return 'short'

    def _predict_open(self, candles):
        rsi = self._RSI(candles)
        macd = self._MACD(candles)
        dema = self._DEMA(candles)
        sar = self._SAR(candles)
        rsima = self._RsiMA(candles)
        predict = []
        if rsi[-2] < 20 and rsi[-1] > 20:
            predict.append(0)
        elif rsi[-2] > 80 and rsi[-1] < 80:
            predict.append(0)
        else:
            predict.append(0)

        if macd[-2] < 0 and macd[-1] > 0:
            predict.append(0)
        elif macd[-2] > 0 and macd[-1] < 0:
            predict.append(0)
        else:
            predict.append(0)

        if candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] < candles['close'][-1]:
            predict.append(0)
        elif candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] > candles['close'][-1]:
            predict.append(0)
        else:
            predict.append(0)

        if sar[-2] > candles['high'][-2] and sar[-1] < candles['low'][-1]:
            predict.append(0)
        elif sar[-2] < candles['low'][-2] and sar[-1] > candles['high'][-1]:
            predict.append(0)
        else:
            predict.append(0)

        if rsima[-2] < 50 and rsima[-1] > 50:
            predict.append(11)
        elif rsima[-2] > 50 and rsima[-1] < 50:
            predict.append(-11)

        if -1 > macd[-2:-1] or macd[-2:-1] > 1:
            pass
            # printplot(candles)
            # print(macd)

        if sum(predict) > 0:
            return 1, sum(predict)
        elif sum(predict) < 0:
            return -1, abs(sum(predict))
        else:
            return 0, 0

    def _predict_close(self, candles):
        rsi = self._RSI(candles)
        macd = self._MACD(candles)
        dema = self._DEMA(candles)
        sar = self._SAR(candles)
        rsima = self._RsiMA(candles)

        predict = []
        if rsi[-2] < 20 and rsi[-1] > 20:
            predict.append(0)
        elif rsi[-2] > 80 and rsi[-1] < 80:
            predict.append(0)
        else:
            predict.append(0)

        if macd[-2] < 0 and macd[-1] > 0:
            predict.append(0)
        elif macd[-2] > 0 and macd[-1] < 0:
            predict.append(0)
        else:
            predict.append(0)

        if candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] < candles['close'][-1]:
            predict.append(0)
        elif candles['low'][-1] < dema[-1] < candles['high'][-1] and candles['open'][-1] > candles['close'][-1]:
            predict.append(0)
        else:
            predict.append(0)

        if sar[-2] > candles['high'][-2] and sar[-1] < candles['low'][-1]:
            predict.append(0)
        elif sar[-2] < candles['low'][-2] and sar[-1] > candles['high'][-1]:
            predict.append(0)
        else:
            predict.append(0)

        if rsima[-2] < 50 and rsima[-1] > 50:
            predict.append(11)
        elif rsima[-2] > 50 and rsima[-1] < 50:
            predict.append(-11)

        if sum(predict) > 0:
            return 1, sum(predict)
        elif sum(predict) < 0:
            return -1, abs(sum(predict))
        else:
            return 0, 0

    def open(self, candles):
        predict, power = self._predict_open(candles)
        if predict == 1:
            return 'long', power
        elif predict == -1:
            return 'short', power
        else:
            return None, None

    def close(self, candles, strategy):  # str long or short
        predict, power = self._predict_close(candles)
        if strategy == 'long' and predict == -1:
            return True, power
        elif strategy == 'short' and predict == 1:
            return True, power
        else:
            return False, False

    def trend(self, candles):
        rsi = self._RSI(candles)
        macd = self._MACD(candles)
        dema = self._DEMA(candles)
        sar = self._SAR(candles)
        trend = 0
        if rsi[-1] > 50:
            trend += 1
        if macd[-1] > 0:
            trend += 1
        if candles['low'][-1] > dema[-1]:
            trend += 1
        if candles['low'][-1] > sar[-1]:
            trend += 1
        if trend > 2:
            return 'bull'
        elif trend < 2:
            return 'bear'


class Agent_poloniex():
    def __init__(self, pair, timeframe, balans, min_candles=candles_minutes, day_candles=candles_days, balans2=0,
                 timeframe2=None, debug=False, debug2=False,
                 needcandless=100, fee=0.001, active_stop_loss=True, acrive_take_profit=True, telegram=False,
                 Trend=None, marketTrade=False, marketAgent=None):
        self.data = min_candles
        self.min_candles = {}
        self.min_candles['open'] = np.asarray([item[1] for item in self.data], dtype='float64')
        self.min_candles['close'] = np.asarray([item[2] for item in self.data], dtype='float64')
        self.min_candles['high'] = np.asarray([item[3] for item in self.data], dtype='float64')
        self.min_candles['low'] = np.asarray([item[4] for item in self.data], dtype='float64')
        self.min_candles['date'] = [int(item[0] / 1000) for item in self.data]
        self.data2 = day_candles
        self.day_candles = {}
        self.day_candles['open'] = np.asarray([item[1] for item in self.data2], dtype='float64')
        self.day_candles['close'] = np.asarray([item[2] for item in self.data2], dtype='float64')
        self.day_candles['high'] = np.asarray([item[3] for item in self.data2], dtype='float64')
        self.day_candles['low'] = np.asarray([item[4] for item in self.data2], dtype='float64')
        self.day_candles['date'] = [int(item[0] / 1000) for item in self.data2]
        self.active_stop_loss = active_stop_loss
        self.acrive_take_profit = acrive_take_profit
        self.debug = debug
        self.debug2 = debug2
        self.telegram = telegram
        self.needcandless = needcandless
        self.pair = pair
        self.timeframe = timeframe
        self.timeframe2 = timeframe2
        self.balans = [balans, balans2]  # [10000,1]
        self.strategy = Strategy()
        self.K = 1.
        self.fee = fee
        self.long = False
        self.long_price = 0
        self.long_amount = 0
        self.short = False
        self.short_price = 0
        self.short_amount = 0
        self.long_proffit = []  # [{'open_price':0, 'close_price':0, 'proffit':0}]
        self.short_proffit = []  # [{'open_price':0, 'close_price':0, 'proffit':0}]
        self.trades_count = {'long': 0, 'short': 0}
        self.long_failed_count = 0
        self.short_failed_count = 0
        self.stop_loss_K = 100.15  # %
        self.take_profit_K = 110.77  # %
        self.trailing_take_profit_K = 0.13  # %
        self.stop_loss = 0
        self.take_profit = 0
        self.trailing_stop = 0
        self.vrem_count = 0
        self.Trend = Trend
        self.marketTrade = marketTrade
        self.marketAgent = marketAgent

    def candles_poloniex(self, start, end, timeframe):
        pair = self.pair
        timeframe = timeframe
        start = int(start)
        end = int(end)
        while True:
            try:
                r = requests.get(
                    'https://poloniex.com/public?command=returnChartData&currencyPair={0}&start={1}&end={2}&period={3}'.format(
                        pair, start, end, timeframe))
                #print(r.url)
                if r.status_code == 200:
                    break
            except Exception:
                pass
        data = r.json()
        # if data['error']:
        #     print(data['error'])
        #     raise KeyboardInterrupt
        candles = {}
        candles['open'] = np.asarray([item['open'] for item in data], dtype='float64')
        candles['close'] = np.asarray([item['close'] for item in data], dtype='float64')
        candles['high'] = np.asarray([item['high'] for item in data], dtype='float64')
        candles['low'] = np.asarray([item['low'] for item in data], dtype='float64')
        candles['date'] = [datetime.datetime.fromtimestamp(item['date']) for item in data]
        return candles

    def candles(self, start, end, timeframe, limit=1000):  # start,end must be INT TimeStamp. limit - INT!
        timeframe_ = {'1m': 60, '5m': 5 * 60, '15m': 15 * 60, '30m': 30 * 60, '1h': 60 * 60, '3h': 60 * 60 * 3,
                      '6h': 60 * 60 * 6, '12h': 60 * 60 * 12}
        pair = self.pair
        for i in timeframe_:
            if timeframe_[i] == timeframe:
                timeframe = i

        start = int(start * 10 ** 3)
        end = int(end * 10 ** 3)

        params = {'start': start, 'end': end, 'limit': limit}
        while True:
            time.sleep(5)
            try:
                r = requests.get('https://api.bitfinex.com/v2/candles/trade:{0}:{1}/hist'.format(timeframe, pair),
                                 params=params)
                # print(r.url)
                # print(len(r.json()))
                if r.status_code == 200:
                    break
            except Exception as err:
                print("\n\n\n\nOshibkanamana on def get_candles!!", err)
                continue
        if len(r.json()) <= limit:
            data = r.json()[::-1]
        else:
            print('Уменьшите период Satrt\End времени!')
            raise ValueError
        candles = {}
        candles['open'] = np.asarray([item[1] for item in data], dtype='float64')
        candles['close'] = np.asarray([item[2] for item in data], dtype='float64')
        candles['high'] = np.asarray([item[3] for item in data], dtype='float64')
        candles['low'] = np.asarray([item[4] for item in data], dtype='float64')
        candles['date'] = [datetime.datetime.fromtimestamp(int(item[0] / 1000)) for item in data]
        return candles

    def start(self):
        start_time = time.time() - self.timeframe * self.needcandless
        end_time = time.time()
        candles = self.candles(end=end_time, start=start_time, timeframe=self.timeframe)
        start_time2 = time.time() - self.timeframe2 * self.needcandless
        end_time2 = time.time()
        high_candles = self.candles(end=end_time2, start=start_time2, timeframe=self.timeframe2)
        self.action_production(candles, high_candles)
        print(self.pair, ' Last price', candles['close'][-1], self.balans, self.strategy.signal(candles),
              ' Now profit: ', self.calc_profit(), "% | ", self.short_proffit, self.long_proffit)
        if self.long:
            now_order = 'Long'
        elif self.short:
            now_order = "Short"
        else:
            now_order = 'None'
        if now_order == 'Long':
            print("    Now order: {} | Open price: {}".format(now_order, self.long_price))
        if now_order == 'Short':
            print("    Now order: {} | Open price: {}".format(now_order, self.short_price))

    def start_poloniex(self):
        start_time = time.time() - self.timeframe * self.needcandless
        end_time = time.time()
        candles = self.candles_poloniex(end=end_time, start=start_time, timeframe=self.timeframe)
        start_time2 = time.time() - self.timeframe2 * self.needcandless
        end_time2 = time.time()
        high_candles = self.candles_poloniex(end=end_time2, start=start_time2, timeframe=self.timeframe2)
        self.action_production(candles, high_candles)
        print(self.pair, ' Last price', candles['close'][-1], self.balans, self.strategy.signal(candles),
              ' Now profit: ', self.calc_profit(), "% | ", self.short_proffit, self.long_proffit)
        if self.long:
            now_order = 'Long'
        elif self.short:
            now_order = "Short"
        else:
            now_order = 'None'
        if now_order == 'Long':
            print("    Now order: {} | Open price: {}".format(now_order, self.long_price))
        if now_order == 'Short':
            print("    Now order: {} | Open price: {}".format(now_order, self.short_price))

    def _candles_days(self, candles):
        can = {}
        x = self._binary_find(self.day_candles['date'], candles['date'][-1])
        if x != None:
            can['close'] = self.day_candles['close'][x - 97:x]
            return can

    def minutes(self, candles):
        start = candles['date'][-1]  # int(candles['time'][-1] / 1000)
        end = start + self.timeframe
        x, y = self._binary_find(self.min_candles['date'], start), self._binary_find(self.min_candles['date'], end)
        candle = {}
        candle['close'] = self.min_candles['close'][x:y]
        for i, v in enumerate(candle['close']):
            if i > 0:
                can = {}
                can['close'] = [v]
                self._trailing(can)
                if self.active_stop_loss:
                    if (self.long and candle['close'][i] < self.stop_loss) or (
                                self.short and candle['close'][i] > self.stop_loss):
                        return v
                if self.acrive_take_profit:
                    if (self.long and candle['close'][i] < self.take_profit and candle['close'][
                            i - 1] > self.take_profit) \
                            or (self.short and candle['close'][i] > self.take_profit and candle['close'][
                                    i - 1] < self.take_profit):
                        return v

    def make_test_candles(self, candles):
        start = candles['date'][-1]
        end = start + self.timeframe
        x, y = self._binary_find(self.min_candles['date'], start), self._binary_find(self.min_candles['date'], end)
        if x == None or y == None:
            print('В файле с минутками нет инфы по свечам из часового файла')
            raise ValueError
        candle = {}
        candle['open'] = self.min_candles['open'][x:y]
        candle['close'] = self.min_candles['close'][x:y]
        candle['high'] = self.min_candles['high'][x:y]
        candle['low'] = self.min_candles['low'][x:y]
        candle['date'] = self.min_candles['date'][x:y]
        C = []
        c = 0
        while c < y-x:
            for key in candle:
                candles[key][-1] = candle[key][c]
            C.append(copy.deepcopy(candles))
            c += 1
        return C

    def _binary_find(self, lst, x):
        p = 0
        r = len(lst) - 1
        answer = None
        if lst[p] <= x <= lst[r]:
            while p <= r:
                aqw = lst[p]
                qw = lst[r]
                if lst[p] <= x < lst[r] and r - p == 1:
                    answer = p - 1
                    break
                elif x == lst[r] and r - p == 1:
                    answer = p
                    break
                q = (p + r) // 2
                if lst[q] == x:
                    answer = q
                    break
                elif lst[q] > x:
                    r = q  # - 1
                elif lst[q] < x:
                    p = q  # + 1
        return answer

    def _stop_loss(self, candles, long=False, short=False):
        if long:
            stl = candles['close'][-1] * (1 - self.stop_loss_K / 100)
            return stl
        if short:
            stl = candles['close'][-1] * (1 + self.stop_loss_K / 100)
            return stl

    def _take_profit(self, candles, long=False, short=False):
        if long:
            stl = candles['close'][-1] * (1 + self.take_profit_K / 100)
            return stl
        if short:
            stl = candles['close'][-1] * (1 - self.take_profit_K / 100)
            return stl

    def calc_profit(self):
        start_blanas = 1
        if self.long_proffit != []:
            for i in self.long_proffit:
                start_blanas *= 1 + i['profit_prc'] / 100
            return round(start_blanas * 100 - 100, 2)
        elif self.short_proffit != []:
            for i in self.short_proffit:
                start_blanas *= 1 + i['profit_prc'] / 100
            return round(start_blanas * 100 - 100, 2)
        else:
            return 0

    def cancel_orders(self):
        if self.long == True:
            self.balans[0] += self.long_amount * self.long_price
            self.balans[1] -= self.long_amount
            self.long = False
            # self.long_reserve -= self.long_amount
            self.long_amount = 0
            self.long_price = 0
            # self.long_index = 0
        if self.short == True:
            self.balans[0] -= self.short_amount
            self.balans[1] += round(self.short_amount / self.short_price, 8)
            self.short = False
            # self.short_reserve = 0
            self.short_amount = 0
            self.short_price = 0
            # self.short_index = 0

    def cancel_orders2(self, candles):
        if self.long == True:
            self.balans[0] += self.long_amount * candles['close'][-1]
            self.balans[1] -= self.long_amount
            self.long = False
            profit = round(self.balans[0] - (self.long_amount * self.long_price / (1 - self.fee)), 8)
            prc = round((((round(self.long_amount * self.long_price / (1 - self.fee), 8) + profit) / round(
                self.long_amount * self.long_price / (1 - self.fee), 8)) - 1) * 100, 2)
            self.long_proffit.append(
                {'open_price': self.long_price, 'close_price': candles['close'][-1], 'amount': self.long_amount,
                 'profit': profit, 'profit_prc': prc})  # += profit
            self.long_amount = 0
            self.long_price = 0
            if self.debug:
                print(
                    'CCC>>>>Close LONG!! pair: {} price:: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, self.long_price, candles['close'][-1], self.long_amount, prc, self.balans))

        if self.short == True:
            self.balans[0] -= self.short_amount
            self.balans[1] += round(self.short_amount / candles['close'][-1], 8)
            self.short = False
            profit = round(self.balans[1] - (self.short_amount / self.short_price / (1 - self.fee)), 8)
            # prc = round((((round(self.short_amount / self.short_price, 8) + profit) / round(self.short_amount / self.short_price, 8)) - 1) * 100,2)
            prc = round((((profit + (self.short_amount / self.short_price / (1 - self.fee))) / (
                self.short_amount / self.short_price / (1 - self.fee))) - 1) * 100, 2)
            self.short_proffit.append(
                {'open_price': self.short_price, 'close_price': candles['close'][-1], 'amount': self.short_amount,
                 'profit': profit, 'profit_prc': prc})  # += profit
            self.short_amount = 0
            self.short_price = 0
            if self.debug:
                print(
                    'CCC<<<<Close Short!! pair: {} price: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, self.short_price, candles['close'][-1], self.short_amount, prc, self.balans))

    def _trailing(self, candles):
        if self.long:
            if candles['close'][-1] > self.stop_loss + self.trailing_stop:
                self.stop_loss = candles['close'][-1] - self.trailing_stop
            if candles['close'][-1] > self.take_profit:  # * (1 + self.trailing_take_profit_K / 100):
                self.take_profit = candles['close'][-1] * (1 - self.trailing_take_profit_K / 100)
        if self.short:
            if candles['close'][-1] < self.stop_loss - self.trailing_stop:
                self.stop_loss = candles['close'][-1] + self.trailing_stop
            if candles['close'][-1] < self.take_profit:  # /  (1 + self.trailing_take_profit_K / 100):
                self.take_profit = candles['close'][-1] / (1 - self.trailing_take_profit_K / 100)

    def _close_long(self, candles):
        if self.balans[1] >= 0:  # self.long_amount:
            if self.marketTrade:
                th = Thread(target=self.marketAgent.open_order, args=('sell', self.balans[1], self.pair,))
                th.start()
                self.balans[0] += round(self.long_amount, 8) * self.marketAgent.get_cur_best_price('sell', self.pair) * (1 - self.fee)
                self.balans[1] -= round(self.long_amount, 8)
                # profit = (candles['close'][-1] - self.long_price) * round(self.long_amount, 8)
                profit = round(self.balans[0] - (self.long_amount * self.long_price / (1 - self.fee)), 8)
                # prc = round((candles['close'][-1] - self.long_price) / self.long_price * 100, 2)
                # prc = round((profit / (self.long_amount * self.long_price / (1-self.fee))) * 100,2)
                prc = round((((round(self.long_amount * self.long_price / (1 - self.fee), 8) + profit) / round(
                    self.long_amount * self.long_price / (1 - self.fee), 8)) - 1) * 100, 2)
                self.long_proffit.append(
                    {'open_price': self.long_price, 'close_price': self.marketAgent.get_cur_best_price('sell', self.pair), 'amount': self.long_amount,
                     'profit': profit, 'profit_prc': prc})  # += profit

                if self.debug:
                    text = 'CCC>>>>Close LONG!! pair: {} DATE: {} price:: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, candles['date'][-1], self.long_price, self.marketAgent.get_cur_best_price('sell', self.pair), self.long_amount, prc,
                        self.balans)
                    print(text)
                    if self.telegram:
                        text = '<code>Закрываем ордер!</code> \n ↑ #Close #Long #{} \nOpened price: {} \nCurent Price: {} \nPROFIT: <strong>{} %</strong>'.format(
                            self.pair, self.long_price, self.marketAgent.get_cur_best_price('sell', self.pair), prc)
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
                self.long = False
                # self.long_reserve -= self.long_amount
                self.long_amount = 0
                self.long_price = 0
                # self.long_index = 0
                self.trades_count['long'] += 1
                self.stop_loss = 0
                self.trailing_stop = 0
                self.take_profit = 0
                self.vrem_count = 0
            else:
                self.balans[0] += round(self.long_amount, 8) * candles['close'][-1] * (1 - self.fee)
                self.balans[1] -= round(self.long_amount, 8)
                # profit = (candles['close'][-1] - self.long_price) * round(self.long_amount, 8)
                profit = round(self.balans[0] - (self.long_amount * self.long_price / (1 - self.fee)), 8)
                # prc = round((candles['close'][-1] - self.long_price) / self.long_price * 100, 2)
                # prc = round((profit / (self.long_amount * self.long_price / (1-self.fee))) * 100,2)
                prc = round((((round(self.long_amount * self.long_price / (1 - self.fee), 8) + profit) / round(
                    self.long_amount * self.long_price / (1 - self.fee), 8)) - 1) * 100, 2)
                self.long_proffit.append(
                    {'open_price': self.long_price, 'close_price': candles['close'][-1], 'amount': self.long_amount,
                     'profit': profit, 'profit_prc': prc})  # += profit

                if self.debug:
                    text = 'CCC>>>>Close LONG!! pair: {} DATE: {} price:: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, candles['date'][-1], self.long_price, candles['close'][-1], self.long_amount, prc,
                        self.balans)
                    print(text)
                    if self.telegram:
                        text = '<code>Закрываем ордер!</code> \n ↑ #Close #Long #{} \nOpened price: {} \nCurent Price: {} \nPROFIT: <strong>{} %</strong>'.format(
                            self.pair, self.long_price, candles['close'][-1], prc)
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
                self.long = False
                # self.long_reserve -= self.long_amount
                self.long_amount = 0
                self.long_price = 0
                # self.long_index = 0
                self.trades_count['long'] += 1
                self.stop_loss = 0
                self.trailing_stop = 0
                self.take_profit = 0
                self.vrem_count = 0
        else:
            if self.debug:
                print("babla net long close ")

    def _close_short(self, candles):
        # balans = self.get_available_balans()
        if self.balans[0] >= 0:  # self.short_amount * candles['close'][-1]:
            if self.marketTrade:
                th = Thread(target=self.marketAgent.open_order, args=('buy', self.balans[0], self.pair,))
                th.start()
                self.balans[1] += round(self.short_amount / self.marketAgent.get_cur_best_price('buy', self.pair) * (1 - self.fee),8)
                self.balans[0] -= round(self.short_amount, 8)
                # profit = round(self.short_amount / candles['close'][-1], 8) - round(self.short_amount / self.short_price, 8)
                profit = round(self.balans[1] - (self.short_amount / self.short_price / (1 - self.fee)), 8)
                # prc = round((((round(self.short_amount / self.short_price, 8) + profit) / round(self.short_amount / self.short_price, 8)) - 1) * 100,2)
                prc = round((((profit + (self.short_amount / self.short_price / (1 - self.fee))) / (
                    self.short_amount / self.short_price / (1 - self.fee))) - 1) * 100, 2)
                self.short_proffit.append(
                    {'open_price': self.short_price, 'close_price': self.marketAgent.get_cur_best_price('buy', self.pair), 'amount': self.short_amount,
                     'profit': profit, 'profit_prc': prc})  # += profit
                if self.debug:
                    text = 'CCC<<<<Close Short!! pair: {} DATE: {} price: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, candles['date'][-1], self.short_price, self.marketAgent.get_cur_best_price('buy', self.pair), self.short_amount, prc,
                        self.balans)
                    print(text)
                    if self.telegram:
                        text = '<code>Закрываем ордер!</code> \n ↓ #Close #Short #{} \nOpened price: {} \nCurent Price: {} \nPROFIT: <strong>{} %</strong>'.format(
                            self.pair, self.short_price, self.marketAgent.get_cur_best_price('buy', self.pair), prc)
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
                self.short = False
                # self.short_reserve -= self.short_amount * candles['close'][-1]
                self.short_amount = 0
                self.short_price = 0
                # self.short_index = 0
                self.trades_count['short'] += 1
                self.stop_loss = 0
                self.take_profit = 0
                self.trailing_stop = 0
                self.vrem_count = 0
            else:
                self.balans[1] += round(self.short_amount / candles['close'][-1] * (1 - self.fee),
                                        8)  # / candles['close'][-1], 8)
                self.balans[0] -= round(self.short_amount, 8)
                # profit = round(self.short_amount / candles['close'][-1], 8) - round(self.short_amount / self.short_price, 8)
                profit = round(self.balans[1] - (self.short_amount / self.short_price / (1 - self.fee)), 8)
                # prc = round((((round(self.short_amount / self.short_price, 8) + profit) / round(self.short_amount / self.short_price, 8)) - 1) * 100,2)
                prc = round((((profit + (self.short_amount / self.short_price / (1 - self.fee))) / (
                    self.short_amount / self.short_price / (1 - self.fee))) - 1) * 100, 2)
                self.short_proffit.append(
                    {'open_price': self.short_price, 'close_price': candles['close'][-1], 'amount': self.short_amount,
                     'profit': profit, 'profit_prc': prc})  # += profit
                if self.debug:
                    text = 'CCC<<<<Close Short!! pair: {} DATE: {} price: Open-{} | Close-{} \ amount: {} PROFIT: {}\nNow balans: {}'.format(
                        self.pair, candles['date'][-1], self.short_price, candles['close'][-1], self.short_amount, prc,
                        self.balans)
                    print(text)
                    if self.telegram:
                        text = '<code>Закрываем ордер!</code> \n ↓ #Close #Short #{} \nOpened price: {} \nCurent Price: {} \nPROFIT: <strong>{} %</strong>'.format(
                            self.pair, self.short_price, candles['close'][-1], prc)
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
                self.short = False
                # self.short_reserve -= self.short_amount * candles['close'][-1]
                self.short_amount = 0
                self.short_price = 0
                # self.short_index = 0
                self.trades_count['short'] += 1
                self.stop_loss = 0
                self.take_profit = 0
                self.trailing_stop = 0
                self.vrem_count = 0
        else:
            if self.debug:
                print("babla net short close")

    def _open_long(self, candles):
        #if self.short == True:
            #self._close_short(candles)
            # if self.balans[0] >= 0:# self.short_amount * self.short_price:
            #     profit = (self.short_price - candles['close'][-1]) * round(self.short_amount, 8)
            #     prc = round((self.short_price - candles['close'][-1]) / self.short_price * 100, 2)
            #     self.short_proffit.append({'open_price':self.short_price, 'close_price':candles['close'][-1], 'amount':self.short_amount, 'profit':profit, 'profit_prc':prc})# += profit
            #     if self.debug:
            #         print('CCC<<<<Close Short!! pair: {} price: {} \ amount: {} PROFIT: {} Reopened long'.format(
            #             self.pair, candles['close'][-1], self.short_amount, profit))
            #     self.short = False
            #     #self.short_reserve -= self.short_amount * candles['close'][-1]
            #     self.short_amount = 0
            #     self.short_price = 0
            #     #self.short_index = 0
            #     self.trades_count['short'] += 1
            #     self.stop_loss = 0
            #     self.trailing_stop = 0
            # else:
            #     if self.debug:
            #         print("babla net short cancel")
        # balans = self.get_available_balans()
        if self.balans[0] > 0:
            if self.marketTrade:
                th = Thread(target=self.marketAgent.open_order, args=('buy', self.balans[0], self.pair,))
                th.start()
                self.long_amount = round(self.balans[0] / self.K / self.marketAgent.get_cur_best_price('buy', self.pair) * (1 - self.fee), 8)
                self.long_price = self.marketAgent.get_cur_best_price('buy', self.pair)
                self.balans[1] += round(self.balans[0] / self.K / self.marketAgent.get_cur_best_price('buy', self.pair) * (1 - self.fee), 8)
                self.balans[0] -= round(self.balans[0] / self.K, 8)
                self.long = True
                self.stop_loss = self._stop_loss(candles, long=True)
                self.take_profit = self._take_profit(candles, long=True)
                self.trailing_stop = self.long_price - self.stop_loss
                if self.debug:
                    text = 'OOO>>>>Open LONG!! pair: {} DATE: {} price: {} \ amount: {}\nNow balans: {}'.format(
                        self.pair,
                        candles[
                            'date'][
                            -1],
                        candles[
                            'close'][
                            -1],
                        self.long_amount,
                        self.balans)
                    print(text)
                    if self.telegram:
                        text = '<i>{}, {}! {}!</i> \n ↑ #Open #Long #{} \nCurent Price: <b>{}</b>'.format(
                            random.choice(generator['1']), random.choice(generator['up1']),
                            random.choice(generator['up2']),
                            self.pair, self.marketAgent.get_cur_best_price('buy', self.pair))
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
            else:
                self.long_amount = round(self.balans[0] / self.K / candles['close'][-1] * (1 - self.fee), 8)
                self.long_price = candles['close'][-1]
                self.balans[1] += round(self.balans[0] / self.K / candles['close'][-1] * (1 - self.fee), 8)
                self.balans[0] -= round(self.balans[0] / self.K, 8)
                self.long = True
                self.stop_loss = self._stop_loss(candles, long=True)
                self.take_profit = self._take_profit(candles, long=True)
                self.trailing_stop = self.long_price - self.stop_loss
                if self.debug:
                    text = 'OOO>>>>Open LONG!! pair: {} DATE: {} price: {} \ amount: {}\nNow balans: {}'.format(self.pair,
                                                                                                                candles[
                                                                                                                    'date'][
                                                                                                                    -1],
                                                                                                                candles[
                                                                                                                    'close'][
                                                                                                                    -1],
                                                                                                                self.long_amount,
                                                                                                                self.balans)
                    print(text)
                    if self.telegram:
                        text = '<i>{}, {}! {}!</i> \n ↑ #Open #Long #{} \nCurent Price: <b>{}</b>'.format(
                            random.choice(generator['1']), random.choice(generator['up1']), random.choice(generator['up2']),
                            self.pair, candles['close'][-1])
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
        else:
            self.long_failed_count += 1
            # if self.debug:
            #     print("babla net long open")

    def _open_short(self, candles):
        # if self.long == True:
        #     self._close_long(candles)
            # if self.balans[1] >= 0:# self.long_amount:
            #     profit = (candles['close'][-1] - self.long_price) * round(self.long_amount, 8)
            #     prc = round((candles['close'][-1] - self.long_price) / self.long_price * 100, 2)
            #     self.long_proffit.append({'open_price':self.long_price, 'close_price':candles['close'][-1], 'amount': self.long_amount, 'profit':profit, 'profit_prc':prc})# += profit
            #     if self.debug:
            #         print('CCC>>>>Close LONG!! pair: {} price: {} \ amount: {} PROFIT: {}\ Reopened Short'.format(
            #             self.pair, candles['close'][-1], self.long_amount, profit))
            #     self.long = False
            #     #self.long_reserve -= self.long_amount
            #     self.long_amount = 0
            #     self.long_price = 0
            #     # self.long_index = 0
            #     self.trades_count['long'] += 1
            #     self.stop_loss = 0
            #     self.trailing_stop = 0
            # else:
            #     if self.debug:
            #         print("babla net long cancel")
        # balans = self.get_available_balans()
        if self.balans[1] > 0:
            if self.marketTrade:
                th = Thread(target=self.marketAgent.open_order, args=('sell', self.balans[1], self.pair,))
                th.start()
                self.short_amount = (self.balans[1] / self.K) * self.marketAgent.get_cur_best_price('sell', self.pair) * (1 - self.fee)
                self.short_price = self.marketAgent.get_cur_best_price('sell', self.pair)
                self.balans[0] += round((self.balans[1] / self.K) * self.marketAgent.get_cur_best_price('sell', self.pair) * (1 - self.fee), 8)
                self.balans[1] -= round(self.balans[1] / self.K, 8)
                self.short = True
                self.stop_loss = self._stop_loss(candles, short=True)
                self.take_profit = self._take_profit(candles, short=True)
                self.trailing_stop = self.stop_loss - self.short_price
                if self.debug:
                    text = 'OOO<<<<Open Short!! pair: {} DATE: {} price:: {} \
                                 amount: {}\nNow balans: {}'.format(self.pair, candles['date'][-1],
                                                                    candles['close'][-1], self.short_amount,
                                                                    self.balans)
                    print(text)
                    if self.telegram:
                        text = '<i>{}, {}! {}!</i> \n ↓ #Open #Short #{} \nCurent Price: <b>{}</b>'.format(
                            random.choice(generator['1']), random.choice(generator['down1']),
                            random.choice(generator['down2']), self.pair, self.marketAgent.get_cur_best_price('sell', self.pair))
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
            else:
                self.short_amount = (self.balans[1] / self.K) * candles['close'][-1] * (1 - self.fee)
                self.short_price = candles['close'][-1]
                self.balans[0] += round((self.balans[1] / self.K) * candles['close'][-1] * (1 - self.fee), 8)
                self.balans[1] -= round(self.balans[1] / self.K, 8)
                self.short = True
                self.stop_loss = self._stop_loss(candles, short=True)
                self.take_profit = self._take_profit(candles, short=True)
                self.trailing_stop = self.stop_loss - self.short_price
                if self.debug:
                    text = 'OOO<<<<Open Short!! pair: {} DATE: {} price:: {} \
                     amount: {}\nNow balans: {}'.format(self.pair,candles['date'][-1],candles['close'][-1],self.short_amount,self.balans)
                    print(text)
                    if self.telegram:
                        text = '<i>{}, {}! {}!</i> \n ↓ #Open #Short #{} \nCurent Price: <b>{}</b>'.format(
                            random.choice(generator['1']), random.choice(generator['down1']),
                            random.choice(generator['down2']), self.pair, candles['close'][-1])
                        for ch in chat_id:
                            bot.send_message(ch, text, parse_mode='HTML')
        else:
            self.short_failed_count += 1

    def action(self, candles):
        lastprice = candles['close'][-1]

        if self.long or self.short:
            self.vrem_count += 1
            # close_price = self.minutes(candles)
            # if close_price != None:
            #     c = {}
            #     c['close'] = [close_price]
            #     if self.long:
            #         self._close_long(c)
            #     elif self.short:
            #         self._close_short(c)
        if candles['date'][-1] == 1522764900:
            print('ass')
        # start = candles['date'][-1] - self.timeframe * 14  # int(candles['time'][-1] / 1000)
        # end = candles['date'][-1] + self.timeframe
        # x, y = self._binary_find(self.min_candles['date'], start), self._binary_find(self.min_candles['date'], end)
        # candle = {}
        # candle['close'] = self.min_candles['close'][x:y]
        # signal = self.strategy.signal3(self.timeframe, candle)

        #C = self.make_test_candles(candles)
        # signal = self.strategy.signal2(candles, self._candles_days(candles))
        signal = self.strategy.nn_signal(candles, self._candles_days(candles))
        signal2 = self.strategy.nn_signal2(candles)
        signal_rsi = self.strategy.signal(candles)

        if signal == 'long' and self.long == False and self.short == False:
            self._open_long(candles)
            if self.debug2:
                self.printplot(candles)
        #
        elif (signal == 'long' or signal_rsi == 'long') and self.long == False and self.short == True:
            if self.Trend == 'up':
                self._close_short(candles)
                self._open_long(candles)
            elif self.Trend == 'down' and candles['close'][-1] / (1 - self.fee*2) < self.short_price:
                self._close_short(candles)
                self._open_long(candles)
            elif self.Trend == None:
                self._close_short(candles)
                self._open_long(candles)
            if self.debug2:
                self.printplot(candles)

        elif signal == 'short' and self.short == False and self.long == False:
            self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

        elif (signal == 'short' or signal_rsi == 'short') and self.short == False and self.long == True:
            if self.Trend == 'up' and candles['close'][-1] * (1 - self.fee*2) > self.long_price:
                self._close_long(candles)
                self._open_short(candles)
            elif self.Trend == 'down':
                self._close_long(candles)
                self._open_short(candles)
            elif self.Trend == None:
                self._close_long(candles)
                self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

        # if self.long and self.strategy._RSI(candles)[-1] > 40 and self.vrem_count >= 1:
        #     self._close_long(candles)
        # if self.short and self.strategy._RSI(candles)[-1] < 60 and self.vrem_count >= 1:
        #     self._close_short(candles)

        if self.long and signal2 == 'close_long' and self.vrem_count > 0:  # and candles["close"][-1] > self.long_price:
            if self.Trend == 'up' and candles['close'][-1] * (1 - self.fee*2) > self.long_price:
                self._close_long(candles)
            elif self.Trend == 'down':
                self._close_long(candles)
            elif self.Trend == None:
                self._close_long(candles)
        if self.short and signal2 == 'close_short' and self.vrem_count > 0:  # and candles["close"][-1] < self.short_price:
            if self.Trend == 'up':
                self._close_short(candles)
            elif self.Trend == 'down' and candles['close'][-1] / (1 - self.fee*2) < self.short_price:
                self._close_short(candles)
            elif self.Trend == None:
                self._close_short(candles)




            # if self.long and candles["close"][-1] < self.long_price and self.vrem_count >= 2:
            #    self._close_long(candles)
            # if self.short and candles["close"][-1] > self.short_price and self.vrem_count >= 2:
            #    self._close_short(candles)
            #
            #
            #
            # if self.long and self.strategy._RSI(candles)[-1] < 15 and self.vrem_count > 1:
            #     self._close_long(candles)
            # elif self.short and self.strategy._RSI(candles)[-1] > 85 and self.vrem_count > 1:
            #     self._close_short(candles)

    def action_production_stable_old(self, candles, high_candles):
        if self.long or self.short:
            self.vrem_count += 1

        signal = self.strategy.nn_signal(candles, high_candles)
        signal_rsi = self.strategy.signal(candles)

        if signal == 'long' and self.long == False and self.short == False:
            self._open_long(candles)
            if self.debug2:
                self.printplot(candles)

        elif (
                        signal == 'long' or signal_rsi == 'long') and self.long == False and self.short == True:  # and candles['close'][-1] > self.stop_loss:# and candles['close'][-1] > self.stop_loss:
            self._close_short(candles)
            self._open_long(candles)
            if self.debug2:
                self.printplot(candles)

        elif signal == 'short' and self.short == False and self.long == False:
            self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

        elif (
                        signal == 'short' or signal_rsi == 'short') and self.short == False and self.long == True:  # and candles['close'][-1] < self.stop_loss:# and candles['close'][-1] < self.stop_loss:
            self._close_long(candles)
            self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

    def action_production(self, candles, high_candles):
        if self.long or self.short:
            self.vrem_count += 1

        signal = self.strategy.nn_signal(candles, high_candles)
        signal2 = self.strategy.nn_signal2(candles)
        signal_rsi = self.strategy.signal(candles)

        if signal == 'long' and self.long == False and self.short == False:
            self._open_long(candles)
            if self.debug2:
                self.printplot(candles)

        elif (
                signal == 'long' or signal_rsi == 'long') and self.long == False and self.short == True:  # and candles['close'][-1] > self.stop_loss:# and candles['close'][-1] > self.stop_loss:
            if self.Trend == 'up':
                self._close_short(candles)
                self._open_long(candles)
            elif self.Trend == 'down' and candles['close'][-1] / (1 - self.fee*2) < self.short_price:
                self._close_short(candles)
                self._open_long(candles)
            elif self.Trend == None:
                self._close_short(candles)
                self._open_long(candles)
            if self.debug2:
                self.printplot(candles)

        elif signal == 'short' and self.short == False and self.long == False:
            self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

        elif (
                signal == 'short' or signal_rsi == 'short') and self.short == False and self.long == True:  # and candles['close'][-1] < self.stop_loss:# and candles['close'][-1] < self.stop_loss:
            if self.Trend == 'up' and candles['close'][-1] * (1 - self.fee*2) > self.long_price:
                self._close_long(candles)
                self._open_short(candles)
            elif self.Trend == 'down':
                self._close_long(candles)
                self._open_short(candles)
            elif self.Trend == None:
                self._close_long(candles)
                self._open_short(candles)
            if self.debug2:
                self.printplot(candles)

        if self.long and signal2 == 'close_long' and self.vrem_count > 2:
            if self.Trend == 'up' and candles['close'][-1] * (1 - self.fee*2) > self.long_price:
                self._close_long(candles)
            elif self.Trend == 'down':
                self._close_long(candles)
            elif self.Trend == None:
                self._close_long(candles)
        if self.short and signal2 == 'close_short' and self.vrem_count > 2:
            if self.Trend == 'up':
                self._close_short(candles)
            elif self.Trend == 'down' and candles['close'][-1] / (1 - self.fee*2) < self.short_price:
                self._close_short(candles)
            elif self.Trend == None:
                self._close_short(candles)

    def printplot(self, candles):
        fig, ax = plt.subplots(3, sharex=True)

        candlestick2_ohlc(ax[0], candles['open'], candles['high'], candles['low'], candles['close'], width=0.6)

        ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))

        def chart_date(x, pos):
            try:
                return candles['date'][int(x)]
            except IndexError:
                return ''

        ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

        fig.autofmt_xdate()
        fig.tight_layout()

        sma = self.strategy._DEMA(candles)
        # print(sma)
        ax[0].plot(sma)

        sar = self.strategy._SAR(candles)
        # print(sar)
        ax[0].plot(sar)

        macdhist = self.strategy._MACD(candles)
        # print(macdhist)
        # ax[1].plot(macd, color="y")
        # ax[1].plot(macdsignal)

        hist_data = []
        for elem in macdhist:
            if not np.isnan(elem):
                v = 0 if np.isnan(elem) else elem
                hist_data.append(v * 100)
        ax[1].fill_between([x for x in range(len(macdhist))], 0, macdhist)

        fastk, fastd = talib.STOCHRSI(candles['close'], timeperiod=14, fastk_period=14, fastd_period=3, fastd_matype=0)
        ax[2].plot(fastk, color="y")
        ax[2].plot(fastd, color="b")

        # RsiMa = self.strategy._RsiMA(candles)
        # c = 0
        # for i, v in enumerate(RsiMa):
        #     if i > 0:
        #         if (RsiMa[i - 1] > 50 and RsiMa[i] < 50) or (RsiMa[i - 1] < 50 and RsiMa[i] > 50):
        #             c += 1
        # print(c)
        # print(RsiMa)
        # ax[2].plot(RsiMa, color="y")

        # FastAtrRsiTL, RsiMa = self.strategy._QQE_NIK(candles)
        # ax[2].plot(FastAtrRsiTL, color="y")
        # ax[2].plot(RsiMa, color="b")

        # FastAtrRsiTL, RsiMa = self.strategy._QQE_NIK(candles)
        # ax[2].plot(FastAtrRsiTL, color="y")
        # ax[2].plot(RsiMa, color="b")


        plt.show()


if __name__ == "__main__":
    pass

    per = 60 * 60 * 12
    b = (24 * 60 * 60) * 60
    print(b)
    start_time = int(time.time()) - b  # 24*60*60

    resource = requests.get(
        "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_BTC&start={}&end=9999999999&period={}".format(
            start_time, per))
    print(resource.url)
    data = json.loads(resource.text)

    quotes = {}
    quotes['open'] = np.asarray([item['open'] for item in data])
    quotes['close'] = np.asarray([item['close'] for item in data])
    quotes['high'] = np.asarray([item['high'] for item in data])
    quotes['low'] = np.asarray([item['low'] for item in data])

    xdate = [datetime.datetime.fromtimestamp(item['date']) for item in data]

    fig, ax = plt.subplots(3, sharex=True)

    candlestick2_ohlc(ax[0], quotes['open'], quotes['high'], quotes['low'], quotes['close'], width=0.6)

    ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))


    def chart_date(x, pos):
        try:
            return xdate[int(x)]
        except IndexError:
            return ''


    ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

    fig.autofmt_xdate()
    fig.tight_layout()

    sma = talib.DEMA(quotes['close'], timeperiod=9)
    print(sma)
    ax[0].plot(sma)

    sar = talib.SAR(quotes['high'], quotes['low'], acceleration=0.02, maximum=0.2)
    print(sar)
    ax[0].plot(sar)

    macd, macdsignal, macdhist = talib.MACD(quotes['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    print(macdhist)
    ax[1].plot(macd, color="y")
    ax[1].plot(macdsignal)

    hist_data = []
    for elem in macdhist:
        if not np.isnan(elem):
            v = 0 if np.isnan(elem) else elem
            hist_data.append(v * 100)
    ax[1].fill_between([x for x in range(len(macdhist))], 0, macdhist)

    # fastk, fastd = talib.STOCHRSI(quotes['close'], timeperiod=14, fastk_period=14, fastd_period=3, fastd_matype=3)


    try:
        RSI = talib.RSI(quotes['close'], 12)
        RSI = list(np.nan_to_num(RSI))
        RSI = np.array(RSI)

        RsiMa = talib.DEMA(RSI, 5)
        RsiMa = np.nan_to_num(RsiMa)
    except Exception as err:
        pass
    c = 0
    for i, v in enumerate(RsiMa):
        if i > 0:
            if (RsiMa[i - 1] > 50 and RsiMa[i] < 50) or (RsiMa[i - 1] < 50 and RsiMa[i] > 50):
                c += 1
    print(c)
    ax[2].plot(RsiMa, color="y")
    # ax[2].plot(fastd, color="b")

    plt.show()

    # f = open('Pair_tBCHUSD_candles_timeframe_15m_fields_26161.csv')
    # candles_ = f.readline()
    # f.close()
    # data = json.loads(candles_)
    # data = data[-int(60*60*24/60/15):]
    # print(len(data))
    #
    # quotes = {}
    # quotes['open'] = np.asarray([item[1] for item in data])
    # quotes['close'] = np.asarray([item[2] for item in data])
    # quotes['high'] = np.asarray([item[3] for item in data])
    # quotes['low'] = np.asarray([item[4] for item in data])
    #
    # xdate = [datetime.datetime.fromtimestamp(int(item[0] / 1000)) for item in data]
    #
    # fig, ax = plt.subplots(3, sharex=True)
    #
    # candlestick2_ohlc(ax[0], quotes['open'], quotes['high'], quotes['low'], quotes['close'], width=0.6)
    #
    # ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))
    #
    #
    # def chart_date(x, pos):
    #     try:
    #         return xdate[int(x)]
    #     except IndexError:
    #         return ''
    #
    #
    # ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))
    #
    # fig.autofmt_xdate()
    # fig.tight_layout()
    #
    # sma = talib.DEMA(quotes['close'], timeperiod=9)
    # print(sma)
    # ax[0].plot(sma)
    #
    # sar = talib.SAR(quotes['high'], quotes['low'], acceleration=0.02, maximum=0.2)
    # ax[0].plot(sar)
    #
    # macd, macdsignal, macdhist = talib.MACD(quotes['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    # ax[1].plot(macd, color="y")
    # ax[1].plot(macdsignal)
    #
    # hist_data = []
    # for elem in macdhist:
    #     if not np.isnan(elem):
    #         v = 0 if np.isnan(elem) else elem
    #         hist_data.append(v * 100)
    # ax[1].fill_between([x for x in range(len(macdhist))], 0, macdhist)
    #
    # fastk, fastd = talib.STOCHRSI(quotes['close'], timeperiod=14, fastk_period=14, fastd_period=3, fastd_matype=3)
    # ax[2].plot(fastk, color="y")
    # ax[2].plot(fastd, color="b")
    #
    # plt.show()
