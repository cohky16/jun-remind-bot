import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
import datetime as dt
from pytz import timezone

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

def getId():
    url = 'https://api.twitch.tv/kraken/search/channels?query='
    channelName = 'kato_junichi0817'
    headers = {
        'Client-ID': os.environ.get("CLIENT_ID"),
        'Accept': 'application/vnd.twitchtv.v5+json'
    }
    response = requests.get(url + channelName, headers=headers)
    return response.json()['channels'][0]['_id']

def getTwitch():
    url = 'https://api.twitch.tv/kraken/streams/'
    channelId = str(getId())
    headers = {
        'Client-ID': os.environ.get("CLIENT_ID"),
        'Accept': 'application/vnd.twitchtv.v5+json'
    }
    response = requests.get(url + channelId, headers=headers)

    result = []

    if response.json()['stream'] is None:
        print('未配信')
    else:
        print('タイトル: ' + str(response.json()['stream']['channel']['status']))
        result.append(str(response.json()['stream']['channel']['status']))
        print('配信URL: ' + str(response.json()['stream']['channel']['url']))
        result.append(str(response.json()['stream']['channel']['url']))
        print('サムネイル: ' + str(response.json()['stream']['preview']['medium']))
        result.append(str(response.json()['stream']['preview']['medium']))
        allDate = str(response.json()['stream']['created_at'])
        tempDateUTC = dt.datetime(int(allDate[0:4]),int(allDate[5:7]),int(allDate[8:10]),int(allDate[11:13]),int(allDate[14:16]),int(allDate[17:19]),1000,tzinfo=dt.timezone.utc)
        tempDate = tempDateUTC.astimezone(timezone('Asia/Tokyo'))
        nowDate = dt.datetime.now().astimezone(timezone('Asia/Tokyo'))
        print('現在時刻：' + str(nowDate) + ' 配信開始：' + str(tempDate))
        difTime = nowDate - tempDate
        if (difTime.seconds > 1):
            return None
        date = str(tempDate.strftime("%Y/%m/%d %H:%M 開始"))
        result.append(date)
        print('ゲーム名: ' + str(response.json()['stream']['channel']['game']))
        if str(response.json()['stream']['channel']['game']) == '':
            result.append('未設定')
        else:
            result.append(str(response.json()['stream']['channel']['game']))

        return result