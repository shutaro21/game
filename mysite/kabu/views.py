from django.shortcuts import render
from django.conf import settings
import requests
import json
import datetime

def graph(request):
    brands = settings.KABU_BRANDS
    td = (datetime.datetime.now() - datetime.datetime.strptime(settings.KABU_BASEDATE,"%Y/%m/%d")).days
    td += 60
    urls = []
    for brand in brands.values():
        urls.append("https://query1.finance.yahoo.com/v8/finance/chart/" + str(brand) + ".T?range=" + str(td) + "d&interval=1d")
    res = []
    for url in urls:
        res.append(requests.get(url).json())
    data = []
    for i, timestamp in enumerate(res[0]["chart"]["result"][0]["timestamp"]):
        d = {}
        d["timestamp"] = datetime.datetime.fromtimestamp(timestamp, datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y/%m/%d")
        d["closeX"] = 0
        for j, r in enumerate(res):
            d["close" + str(j+1)] = r["chart"]["result"][0]["indicators"]["quote"][0]["close"][i] * 100
            d["closeX"] += r["chart"]["result"][0]["indicators"]["quote"][0]["close"][i] * 100
        data.append(d)

    return render(request, 'kabu/graph.html', {"brands":brands.keys,"data":json.dumps(data),"basedate":settings.KABU_BASEDATE,"basevalue":settings.KABU_BASEVALUE,})
