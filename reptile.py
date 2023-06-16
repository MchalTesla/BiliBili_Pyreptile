import requests
from PyQt5.QtCore import QThread, pyqtSignal
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import user_agent
from mysql_concat import mysql_concat
from GetDanmu import GetDanmu
from header import headers

class ReptileThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, db, keyword, number, interval):
        super().__init__()
        self.db = db
        self.keyword = keyword
        self.number = number
        self.videocount = 0
        self.danmucount = 0
        self.stop_flag = False
        self.progress_step = 100 // self.number
        self.interval = interval

    def run(self):
        progress_value = 0
        for i in range(self.number):
            if self.stop_flag:
                break
            tempurl = "https://search.bilibili.com/all?keyword={0}&from_source=nav_search&page={1}&order=totalrank&duration=0&tids_1=0&single_column=0".format(
                self.keyword, i + 1)
            self.reptile(url=tempurl, db=self.db, progress_value=progress_value)
            progress_value = (i + 1) * 100 // self.number
        self.finished.emit()

    def reptile(self, url, db, progress_value):
        print(headers)
        response = requests.get(url=url, headers=headers)
        print("Response state: " + str(response.status_code))
        features = "html.parser"
        soup = BeautifulSoup(response.text, features=features)
        cursor = db.cursor()
        find_num = 0
        for link in soup.find_all('a'):
            if link.get('href') is not None:
                if re.match('.*/video/([0-9a-zA-Z]+)', link.get('href')) is not None:
                    find_num += 1
        i = 0
        for link in soup.find_all('a'):
            if self.stop_flag:
                break
            if link.get('href') is not None:
                vid = re.match('.*/video/([0-9a-zA-Z]+)', link.get('href'))
                if vid is not None:
                    time.sleep(self.interval)
                    info = GetDanmu.get_info(vid.group(1))
                    danmu = GetDanmu.get_danmu(info)
                    sql = "SELECT COUNT(*) from video where bvid=%s"
                    values = (info["bvid"])
                    cursor.execute(sql, values)
                    if cursor.fetchone()[0] > 0: continue
                    sql = "INSERT INTO video(bvid, aid, videourl, title, numberofvideo, numberofdanmu) VALUES (%s, %s, %s, %s, %s, %s)"
                    values = (info["bvid"], info["aid"], info["videourl"], info["title"], info["numberofvideo"],
                              info["numberofdanmu"])
                    cursor.execute(sql, values)
                    self.videocount = self.videocount + 1
                    for dm in danmu:
                        sql = "INSERT INTO danmu(bvid, cid, danmu) VALUES (%s, %s, %s)"
                        values = (info["bvid"], dm[0], dm[1])
                        cursor.execute(sql, values)
                        self.danmucount = self.danmucount + 1

                    i = i+1

            temp_progress_value = progress_value + ((i+1)*self.progress_step//find_num)
            self.progress.emit(temp_progress_value)
    def stop(self):
        self.stop_flag = True