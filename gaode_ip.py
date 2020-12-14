import xlrd
import requests
import json
import pymongo
import random
"""
    爬取高德地图的全国各个城市的天气预报信息，练习ip代理的使用方法
"""

class GaoDe:
    def __init__(self):
        self.base_url = 'https://www.amap.com/service/weather?adcode='
        self.headers ={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        self.MONGO_URL = 'localhost'
        self.MONGO_DB = 'new_day'
        self.MONGO_TABLE = 'gaodetianqi'
        self.proxy_ips=[]
    def get_url(self,row):
        name = row[0] #城市名字
        adcode = row[1]
        url = self.base_url + str(adcode)
        return name,url

    def get_data(self,url):
        proxy_ip = random.choice(self.proxy_ips)
        proxies = {
            "http": "http://%(proxy)s/" % {"proxy": proxy_ip},
            "https": "http://%(proxy)s/" % {"proxy": proxy_ip}
        }

        print('使用代理：',proxy_ip)
        try:
            response = requests.get(url=url,headers = self.headers,proxies=proxies,timeout=3)
            response = json.loads(response.text)
            if response.get('data').get('result') =='true':
                return response.get('data').get('data')
            else:
                print("无该城市天气情况")
        except:
            print('代理失效')
            self.del_proxies(proxy_ip)


    def parse_data(self,datas):
        dict = {}
        for i in range(2):
            details_dict = {}
            data = datas[i]
            details = data.get('forecast_data')[0]
            forecast_date = data.get('forecast_date')
            max_temp = details.get('max_temp')  #最高温度
            min_temp = details.get('min_temp')  #最低温度
            weather_name = details.get('weather_name')  #天气状态
            wind_direction_desc = details.get('wind_direction_desc')    #风向
            wind_power_desc = details.get('wind_power_desc')    #风速等级
            details_dict['最高温度']=max_temp
            details_dict['最低温度']=min_temp
            details_dict['天气状态']=weather_name
            details_dict['风向']=wind_direction_desc
            details_dict['风速等级']=wind_power_desc
            dict[forecast_date]=details_dict
        return dict


    # 获取高德地图上的城市编码
    def get_adcode(self):
        wb = xlrd.open_workbook('data/AMap_adcode_citycode.xlsx') #编码由高德官方提供
        sh1 =wb.sheet_by_index(0)
        for i in range(1,sh1.nrows):
            rows = sh1.row_values(i)
            yield rows

    def save_mongdb(self,result):
        client = pymongo.MongoClient(self.MONGO_URL)
        db =client[self.MONGO_DB]
        try:
            if db[self.MONGO_TABLE].insert(result):
                print('存储到MongoDB成功', result)
        except:
            print('存储到MongoDb失败', result)

    def get_proxies(self,api_url):
        response = requests.get(api_url).text
        data = json.loads(response)
        self.proxy_ips = data.get('data').get('proxy_list')


    def del_proxies(self,proxy_ip):
        self.proxy_ips.remove(proxy_ip)
        print('已移除{}，剩余代理数量{}'.format(proxy_ip,len(self.proxy_ips)))

if __name__ == '__main__':
    gaode = GaoDe()
    gaode.get_proxies(api_url='http://dev.kdlapi.com/api/getproxy/…………')#填入ip代理接口网址，本次使用快代理
    adcode = gaode.get_adcode() #返回一个城市编码迭代器
    for i in adcode:
        name_url = gaode.get_url(i) #返回一个（城市名，编码）的元组
        data = gaode.get_data(name_url[1])
        # time.sleep(0.5)
        if data:
            list = gaode.parse_data(datas=data)
            dict ={name_url[0]:list}
            gaode.save_mongdb(result=dict)



