# -*- coding: utf-8 -*-
# @Time    : 2019/10/21 3:46 PM
# @Author  : python-小智！！
# @FileName: qq_music.py
# @Software: IntelliJ IDEA

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import json
import requests
import os


class QqMusic:
    def __init__(self):
        # 设置 chrome 无界面化模式
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        chrome_driver = "/Users/xiaozhi/Downloads/chromedriver" # 指定位置
        self.header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "accept-language": "zh-CN,zh;q=0.9",
            "referer": "https://y.qq.com/n/yqq/toplist/26.html",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
        }
        self.driver = webdriver.Chrome(chrome_driver, options=self.chrome_options)

    def loading_music(self):
        """
        等到列表里面的歌曲 加载完成后在处理

        # 等待元素出现在DOM
        WebDriverWait(self._driver).until(EC.presence_of_element_located((By.ID, value)))

        # 等待元素显示在页面
        WebDriverWait(self._driver,10).until(EC.visibility_of_element_located((By.NAME, value)))

        # 等待元素从页面消失
        WebDriverWait(self._driver, 10, 0.2).until_not(EC.visibility_of_element_located((By.CLASS_NAME, value))))

        # 等待页面的title显示
        WebDriverWait(self._driver, 5,0.2).until(EC.title_contains(title))

        一次查找多个元素 (这些方法会返回一个list列表):
        find_elements_by_name
        find_elements_by_xpath
        find_elements_by_link_text
        find_elements_by_partial_link_text
        find_elements_by_tag_name
        find_elements_by_class_name
        find_elements_by_css_selector
        :return:
        """
        self.driver.get("https://y.qq.com/n/yqq/toplist/26.html")
        print(self.driver.title)
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "songlist__songname_txt")))
        lists = self.driver.find_elements_by_class_name("songlist__songname_txt")
        pattern = re.compile(r"https://y.qq.com/n/yqq/song/(\S+).html") # 取出每首歌的具体链接
        for i in range(len(lists)):
            li = lists.__getitem__(i)
            a = li.find_element_by_class_name("js_song")
            href = a.get_attribute("href")
            music_name = a.get_attribute("title")
            m = pattern.match(href)
            yield m.group(1), music_name

    def cut_download_url(self):
        """
        筛选和查找下载的url
        :return:
        """
        for music_url, music_name in self.loading_music():
            data = json.dumps({"req": {"module": "CDN.SrfCdnDispatchServer", "method": "GetCdnDispatch",
                                         "param": {"guid": "3802082216", "calltype": 0, "userip": ""}
                                       },
                               "req_0": {
                                        "module": "vkey.GetVkeyServer", "method": "CgiGetVkey",
                                        "param": {
                                            "guid": "3802082216", "songmid": [f'{music_url}'],
                                            "songtype": [0], "uin": "0", "loginflag": 1, "platform":"20"
                                        }
                                    }, "comm": {"uin": 0, "format": "json", "ct": 24, "cv": 0}})
            url = "https://u.y.qq.com/cgi-bin/musicu.fcg?callback=getplaysongvkey3131073469569151&" \
                  "g_tk=5381&jsonpCallback=getplaysongvkey3131073469569151&loginUin=0&hostUin=0&" \
                  f"format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data={data}"
            response = requests.get(url=f"{url}",
                                    headers=self.header)
            html = response.text
            # music_json = json.loads(re.findall(r'^\w+\((.*)\)$',html)[0])
            music_json = html.split("(")[1].split(")")[0]
            music_json = json.loads(music_json)
            assert isinstance(music_json, dict)
            # print(type(music_json))
            req = music_json['req']['data']
            sip = req["sip"][-1]
            purl = music_json['req_0']['data']['midurlinfo'][0]['purl']
            url = f"{sip}{purl}"
            yield url, music_name

    def downloading(self, url, music_name):
        """
        开始下载
        :param url:
        :param music_name:
        :return:
        """
        res = requests.get(f"{url}")
        chunk_size = 1024
        # content_size = int(res.headers['content-length'])
        if not os.path.exists("qq_music"):
            os.mkdir("qq_music")
        with open(f"qq_music/{music_name}.m4a", 'wb') as f:
            # pbar = tqdm(total=int(content_size/1024))
            for data in res.iter_content(chunk_size=chunk_size):
                f.write(data)
                # pbar.update()

    def run(self):
        downloads = [x for x in self.cut_download_url()]
        pbar = tqdm(total=len(downloads))
        for url, music_name in downloads:
            self.downloading(url, music_name)
            pbar.update()


QqMusic().run()
