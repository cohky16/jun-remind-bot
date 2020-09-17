import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
import datetime as dt

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
        #TODO:日付エンコードする
        allDate = str(response.json()['stream']['channel']['updated_at'])
        print('取得時間: ' + str(allDate))
        tempDate = dt.datetime(int(allDate[0:4]),int(allDate[5:7]),int(allDate[8:10]),int(allDate[11:13]),int(allDate[14:16]),int(allDate[17:19]))
        date = tempDate.strftime("%Y/%m/%d %H:%M 開始")
        print('配信開始時間: ' + str(date))
        result.append(str(date))
        print('ゲーム名: ' + str(response.json()['stream']['channel']['game']))
        result.append(str(response.json()['stream']['channel']['game']))

        return result