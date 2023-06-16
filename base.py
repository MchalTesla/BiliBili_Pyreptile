import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import user_agent
from mysql_concat import mysql_concat
from GetDanmu import GetDanmu
from header import headers
from reptile import bilireptile



url = "https://search.bilibili.com/all?vt=15890947&keyword={search}&from_source=webtop_search&spm_id_from=333.1007&search_source=5&page={page}&o={iter}"
seach = input('搜索框：')
pages = int(input('搜索页数：'))
mysqlconcat = mysql_concat()
db = mysqlconcat.getdb()
videocount = 0
danmucount = 0

for i in range(pages):
    tempurl = url.format(search=seach, page=str(i), iter=str(i*30))
    print(tempurl)
    bili = bilireptile()
    bili.reptile(url=url, db=db)
    videocount = videocount + bili.videocount
    danmucount = danmucount + bili.danmucount

print("共爬取了 "+str(videocount)+" 个视频, "+str(danmucount)+" 个弹幕")
