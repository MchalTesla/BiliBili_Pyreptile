import re

import requests


class GetDanmu:

    def get_info(vid):
        url = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={vid}"
        response = requests.get(url)
        response.encoding = "utf-8"
        data = response.json()
        info = {}
        info["title"] = data["data"]["View"]["title"]
        info["numberofdanmu"] = data["data"]["View"]["stat"]["danmaku"]
        info["numberofvideo"] = data["data"]["View"]["videos"]
        info["aid"] = data["data"]["View"]["aid"]
        info["bvid"] = data["data"]["View"]["bvid"]
        info["videourl"] = "https://www.bilibili.com/video/{}/".format(info["bvid"])
        info["cid"] = [dic["cid"] for dic in data["data"]["View"]["pages"]]
        if info["numberofvideo"] > 1:
            info["child"] = [dic["part"] for dic in data["data"]["View"]["pages"]]
        for k, v in info.items():
            print(k + ":", v)
        return info

    def get_danmu(info):
        all_dms = []
        dms = []
        for i, cid in enumerate(info["cid"]):
            url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
            response = requests.get(url)
            response.encoding = "utf-8"
            data = re.findall('<d p="(.*?)">(.*?)</d>', response.text)
            for d in data:
                dms.append([cid, d[1]])
            # dms = [d[1] for d in data]
            # if info["numberofvideo"] > 1:
            #     print("cid:", cid, "弹幕数:", len(dms), "子标题:", info["child"][i])
            all_dms += dms
        print(f"共获取弹幕{len(all_dms)}条！")

        return all_dms
