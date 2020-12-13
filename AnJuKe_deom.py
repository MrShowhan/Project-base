import pymongo
import requests
import re
import time
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont
import base64
import string
from io import BytesIO
from urllib.parse import quote
class AnJuKe:
    def __init__(self):
        base_url = 'https://gz.zu.anjuke.com/fangyuan/?t=1&from=0&comm_exist=on&kw={}'.format(input("请输入小区名字、地址……:"))
        # 将url中带的中文进行转码，而特殊符号不变
        self.decode_url = quote(base_url, safe=string.printable)
        self.total_list=[]
        self.headers ={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'cookie': 'aQQ_ajkguid=0B31434C-A6A9-914A-3016-EFD37A5B5EF8; ctid=12; id58=e87rkF/CB/lzbhvABkTxAg==; _ga=GA1.2.1358634196.1606551544; 58tj_uuid=7538498d-e8c1-4e2a-8563-70649d66aa59; new_uv=1; als=0; cmctid=3; __guid=63061881.1974302922811620400.1607264889348.2612; wmda_uuid=1d51ca6a1baaf9e97cc1e14c56cdc27f; wmda_new_uuid=1; wmda_visited_projects=%3B6289197098934; xxzl_cid=c7dccbd87abc46aaa661b924ba544ed2; xzuid=cdab9516-10f3-448b-a671-a2558c149344; lps=https%3A%2F%2Fgz.zu.anjuke.com%2Ffangyuan%2F%3Ft%3D1%26from%3D0%26comm_exist%3Don%26kw%3D%25E5%2585%2583%25E4%25B8%258B%25E7%2594%25B0%25E6%259D%2591%7C; sessid=B9487E08-46C9-FEB4-DDF9-88D7AEC09043; obtain_by=2; twe=2; monitor_count=16; xzfzqtoken=Cw%2Fgkwi39%2Fn6tp%2FsZR42Z3u8YRwoatsgK5ZGcGEzQmqCXsfHq0kiHsbzIE8ZjK6Ain35brBb%2F%2FeSODvMgkQULA%3D%3D'
        }

        # 连接数据库
        MONGO_URl = 'localhost'
        MONGO_DB = 'test'  # 数据库名
        self.MONGO_TABLE = 'zufang'  # 表名
        client = pymongo.MongoClient(MONGO_URl)
        self.db = client[MONGO_DB]

    # def __repr__(self):
    #     print(str(self.params))



    #访问列表网页并提取所有搜索到的房源连接
    def get_total_link(self,url):
        response = requests.get(url=url,headers = self.headers,timeout=2)
        soup = BeautifulSoup(response.text, 'lxml')
        next_page_url = soup.find('a', class_="aNxt")
        if next_page_url != None:
            links = soup.find_all('div',class_="zu-itemmod")
            for link in links:
                self.total_list.append(link['link'])
            new_url = next_page_url.get('href')
            print('翻页了')
            self.get_total_link(new_url)
        else:
            links = soup.find_all('div', class_="zu-itemmod")
            for link in links:
                if 'list_select_recommend' not in link['_soj']: #去除非指定区域的推荐房源
                    self.total_list.append(link['link'])

        return self.total_list


#访问详细网页
    def ask_url(self,url):
        response = requests.get(url=url,headers = self.headers,timeout=2)
        return (response.text)

#   原网页加密字体替换，使网页源代码可视化
    def parse_response(self,response,newmap):
        for key, value in newmap.items():
            key = key.replace('0x', '&#x') + ';'
            if key in response:
                response = response.replace(key, str(value))
        return response

#   字体解密
    def parse_font(self,response):
        base64_font = re.search(r"base64,(.*?)'\)",response,flags=re.S).group(1)#匹配加密字符串
        b = base64.b64decode(base64_font)   #bas64解密，返回二进制文件
        # with open('font3.woff','wb')as f:   #把解密后的文件写入成woff字体文件
        #     f.write(b)
        # font = TTFont('font3.woff')
        # font.saveXML('bas64_font3.xml')     #使用TTFont工具把woff字体文件转换成可读的xml文件，方便对字体映射关系进行分析
        tf = TTFont(BytesIO(b))                #实例化
        bestcmap = tf.getBestCmap()            #获取cmap节点code与name值映射, 返回为字典
        newmap = dict()
        for key in bestcmap.keys():
            value = int(re.search(r'(\d+)', bestcmap[key]).group(1)) - 1    #通过分析XML文件可得出映射规律，name值末位数-1，比较简单
            key = hex(key)                      #TTFont.get方法返回的key值为十进制，需重新编码。
            newmap[key] = value                 #生成最终映射关系的字典newmap
        return newmap

#提取网页数据
    def get_data(self,html):
        house_dict = {}
        soup = BeautifulSoup(html,'lxml')
        house_dict['标题'] = soup.find('div',class_="strongbox").get_text()        #标题
        house_dict['费用'] = soup.find('li',class_="full-line cf").get_text().replace('\n',' ')   #租金
        for house_info_item in soup.find_all('li',class_='house-info-item'):        #通过遍历提取每一项具体的房屋信息
            model = house_info_item.get_text().replace('\n','')                     #提取文本并转换成单行字符串
            model = "".join(model.split())                                          #去除空格和\xa0
            key,value = model.split("：")                                           #拆分字符串
            house_dict[key]=value
        list1,list2 = [],[]
        [list1.append(i.find('div',class_='peitao-info').get_text()) for i in soup.find_all('li',class_='peitao-item has')]
        house_dict['已有配套'] = list1  #通过列表推导式把所有配套信息整合成列表
        # 无配套设施 = 全部配套 - 已有配套
        [list2.append(i.find('div', class_='peitao-info').get_text()) for i in soup.find_all('li', class_='peitao-item') if i.find('div', class_='peitao-info').get_text() not in list1]
        house_dict['无配套'] = list2
        if soup.find('div',class_='auto-general'):
            house_dict['房屋概况'] = soup.find('div',class_='auto-general').get_text().strip()
        else:
            house_dict['房屋概况'] = '无'
        if soup.find(text='出租要求'):    #判断是否有出租要求
            house_dict['出租要求'] = soup.find(text='出租要求').parent.parent.next_sibling.next_sibling.get_text().strip()  #无法通过标签直接定位只能通过节点关系定位
        return house_dict

    # 存入数据库
    def save_url_to_Mongo(self,result):
        try:
            if self.db[self.MONGO_TABLE].insert_one(result):
                print('存储到MongoDB成功', result)
        except Exception:
            print('存储到MongoDb失败', result)


if __name__ == '__main__':
    anjuke = AnJuKe()
    link_list = anjuke.get_total_link(anjuke.decode_url)
    print('一共获取到{}条房源信息'.format(len(link_list)))
    if len(link_list) > 0:
        for i in link_list:
            time.sleep(2)
            response = anjuke.ask_url(i)
            newmap = anjuke.parse_font(response)
            html = anjuke.parse_response(response,newmap)
            house_dict = anjuke.get_data(html)
            anjuke.save_url_to_Mongo(house_dict)
    else:
        print('无附近房源')



