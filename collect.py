import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
import datetime as dt
from pytz import timezone

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

def getTwitch():
    # トークン取得
    token = getToken()
    checkError(token)
    accessToken = token['access_token']

    # チャンネル情報取得
    tempChannel = getId(accessToken)
    checkError(tempChannel)
    channel = tempChannel['data'][0]

    # 配信情報取得
    tempResponse = getLive(accessToken, channel['id'])
    checkError(tempResponse)

    print('✅配信情報一覧')
    if not tempResponse['data']:
        print('未配信')
        return None
    else:
        result = []
        response = tempResponse['data'][0]
        # タイトル
        title = response['title'].strip()
        print('タイトル: ' + title)
        result.append(title)

        # 配信URL
        url = 'https://www.twitch.tv/' + channel['display_name']
        print('配信URL: ' + url)
        result.append(url)

        # サムネイル
        thumnail = response['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
        print('サムネイル: ' + thumnail)
        result.append(thumnail)

        # 日付
        date = getDate(response)
        if date is None:
            return None
        else:
            print('配信開始時刻: ' + date)
            result.append(date)

        # カテゴリ名
        if response['game_id']:
            tempGameTitle = getGame(accessToken, response['game_id'])
            checkError(tempGameTitle)
            gameTitle = tempGameTitle['data'][0]['name']

            if gameTitle is None:
                print('ゲーム名: 未取得')
                result.append('未取得')
            else:
                print('ゲーム名: ' + gameTitle)
                result.append(gameTitle)
        else:
            print('ゲーム名: 未設定')
            result.append('未設定')
        return result

def getToken():
    print('✅トークン取得')
    url = 'https://id.twitch.tv/oauth2/token'
    data = {
        'client_id': os.environ.get("CLIENT_ID"),
        'client_secret': os.environ.get("CLIENT_SECRET"),
        'grant_type': 'client_credentials',
        'scope': 'channel:read:stream_key'
    }

    response = requests.post(url, data=data).json()
    print(response)
    return response

def getId(token):
    print('✅チャンネル取得')
    url = 'https://api.twitch.tv/helix/search/channels?query='
    channelName = 'kato_junichi0817'
    headers = {
        'Client-ID': os.environ.get("CLIENT_ID"),
        'Authorization': 'Bearer ' + token
    }

    response = requests.get(url + channelName, headers=headers).json()

    return response

def getLive(token, channelId):
    print('✅配信取得')
    url = 'https://api.twitch.tv/helix/streams'
    headers = {
        'Client-ID': os.environ.get("CLIENT_ID"),
        'Authorization': 'Bearer ' + token
    }
    params = '?user_id=' + channelId

    response = requests.get(url + params, headers=headers).json()

    return response

def getDate(response):
    allDate = response['started_at']
    tempDateUTC = dt.datetime(int(allDate[0:4]), int(allDate[5:7]), int(allDate[8:10]), int(
        allDate[11:13]), int(allDate[14:16]), int(allDate[17:19]), 1000, tzinfo=dt.timezone.utc)
    tempDate = tempDateUTC.astimezone(timezone('Asia/Tokyo'))
    nowDate = dt.datetime.now().astimezone(timezone('Asia/Tokyo'))
    difTime = nowDate - tempDate
    if (difTime.seconds > 60):
        print('＜通知済＞')
        return None
    else:
        date = str(tempDate.strftime("%Y/%m/%d %H:%M 開始"))
    return date

def getGame(token, id):
    print('✅ゲーム名取得')
    url = 'https://api.twitch.tv/helix/games'
    headers = {
        'Client-ID': os.environ.get("CLIENT_ID"),
        'Authorization': 'Bearer ' + token
    }
    params = '?id=' + id

    response = requests.get(url + params, headers=headers).json()
    print(response)
    return response

def checkError(response):
    if ('status' in response.keys() and response['status'] != 200) and 'message' in response.keys():
        print('❌エラー： ' + response['message'])
        raise ValueError(response['message'])