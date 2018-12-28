#!/usr/bin/python3
#! _*_ coding: UTF-8 _*_
import requests
import urllib.request, http.client
import json
import urllib
from configobj import ConfigObj

configs = ConfigObj('configs.conf')
server = 'api-lk-ofd'
ver = 'v2'

class OFD:
    def __init__(self,server,ver,login,password,integrator_ID):
        self.server = server
        self.server2 = 'api-tlk-ofd'
        self.ver = ver
        self.login = login
        self.password = password
        self.integrator_ID = integrator_ID

    def get_token(self):

        payload = {
    "login": self.login,
    "password": self.password
        }
        payload = json.dumps(payload)
        headers = {"Content-type": "application/json",
                   "Integrator-ID": self.integrator_ID}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/Login'.format(server=self.server,ver=self.ver)
        #print(prepare)
        response = requests.post(prepare,data=payload,headers=headers)
        # print(response)
        # print(response.json())

        return response.json()['sessionToken']

    def call_api(self,method, **kwargs):
        session_token = self.get_token()
        params = {}
        if kwargs:
            params.update(kwargs)
        #payload = json.dumps(payload)
        headers = {
                   "Session-Token": session_token}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/{method}'.format(server=self.server,ver=self.ver,method=method)
        #print(prepare,params)
        response = requests.get(prepare,params=params,headers=headers)
        #print(response)
        #print(response.json())
        return response.json()

    def get_DepartmentList(self, **kwargs):
        session_token = self.get_token()
        headers = {
                   "Session-Token": session_token}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/DepartmentList'.format(server=self.server,ver=self.ver)
        #print(prepare)
        response = requests.get(prepare,headers=headers)
        #print(response)
        #print(response.json())

        return response.json()

    def get_AccountList(self):
        session_token = self.get_token()
        headers = {
                   "Session-Token": session_token}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/AccountList'.format(server=self.server,ver=self.ver)
        #print(prepare)
        response = requests.get(prepare,headers=headers)
        #print(response)
        #print(response.json())
        return response.json()

    def get_OutletList(self):
        session_token = self.get_token()
        headers = {
                   "Session-Token": session_token}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/OutletList'.format(server=self.server,ver=self.ver)
        #print(prepare)
        response = requests.get(prepare,headers=headers)
        #print(response)
        #print(response.json())
        return response.json()

    def get_OutletInfo(self, **kwargs):
        session_token = self.get_token()
        payload = {}
        if kwargs:
            payload.update(kwargs)
        #payload = json.dumps(payload)
        headers = {
                   "Session-Token": session_token}
        prepare = 'https://{server}.taxcom.ru/API/{ver}/OutletInfo'.format(server=self.server,ver=self.ver)
        #print(prepare)
        response = requests.get(prepare,params=payload,headers=headers)
        #print(response)
        #print(response.json())
        return response.json()

    def get_KKTList(self,id,**kwargs):
        """
        np Фильтр по признаку наличия проблемы:
            OK – Нет проблем
            Warning – Предупреждение
            Problem – Есть проблема
        pn Номер страницы результатов (если не передан, то возвращается первая страница результатов)
        ps Кол-во результатов на странице (1-100)
        """
        return self.call_api('KKTList',id=id)

    def shift_list(self, fnFactoryNumber, begin, end):
        return self.call_api('ShiftList', fn=fnFactoryNumber, begin=begin, end=end)

    def shift_info(self, dict_): #{fnFactoryNumber : shift}
        fnFactoryNumber, shift = list(dict_.items())[0][0], list(dict_.items())[0][1]
        return self.call_api('ShiftInfo', fn=fnFactoryNumber, shift=shift)

test = OFD(server,ver, **configs['ofd-taxcom'])
if __name__ == '__main__':

        # print(test.get_token())
        # print(test.get_markets('DWhSl5CPOUGGb_Comh0yqrZqrNqjPUlFhXWYgbUnKQ'))
        # print(test.get_markets('80Vpmt707bLNTC5tE9BvQJihzjjnToTXz9EjFYr1'))
    print(test.get_DepartmentList())
    print(test.get_AccountList())
    #####print(test.get_OutletList())
    print(test.get_OutletInfo(id='7f8639df-195f-4d2a-b0a3-3831baf46ddc'))
    print(test.call_api('OutletList',np='OK'))
    #print(test.get_KKTList('84ad0155-cd76-4883-9992-f13e3aaac41d'))
    print(test.call_api('KKTList',id='84ad0155-cd76-4883-9992-f13e3aaac41d'))
    print('KKTInfo', test.call_api('KKTInfo',fn='8712000101084579')) #'fnFactoryNumber': '8712000101084579'
    print('ShiftList', test.call_api('ShiftList',fn='8712000101084579',begin='2018-01-30T10:00:00',end='2018-01-30T22:00:00'))
    print('ShiftInfo', test.call_api('ShiftInfo',fn='8712000101084579',shift=156)) #'shiftNumber': 156,
    print('DocumentList', test.call_api('DocumentList',fn='8712000101084579',shift=156)) #,shift=156,type=3
    print('DocumentInfo', test.call_api('DocumentInfo',fn='8712000101084579',fd='8561'))#'fdNumber': 8561,'fdNumber': 8563,
    print('DocumentURL', test.call_api('DocumentURL',fn='8712000101084579',fd='8561'))
    #print("https://api-lk-ofd.taxcom.ru/API/v2/ShiftInfo  {'fn': '8710000100982637', 'shift': 204}\n",test.call_api('ShiftInfo',fn='8710000100982637',shift=204))
    print('!!!!!!!!!!!!!!DocumentInfo', test.call_api('DocumentInfo', fn='8710000100982637', fd=6912))
