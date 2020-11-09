from linebot import LineBotApi
from linebot.models import TextSendMessage, FlexSendMessage
from linebot.exceptions import InvalidSignatureError
import collect
import time
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def twitchMain(oldLiveTime):
    try:
        twitchResultList = collect.getTwitch(oldLiveTime)
        if checkTwitch(twitchResultList):
            sendMessage(twitchResultList, "Twitch")
    except ValueError as e:
        print(e)

def checkTwitch(resultList):
    print("✅配信チェック: " + str(resultList))
    if resultList is not None:
        return True
    return False

def sendMessage(resultList, str):

    message = {
        "type": "flex",
        "altText": "「" + resultList[0] + "」が開始しました",
        "contents": {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": resultList[2],
                    "size": "full",
                    "aspectRatio": "5:2",
                    "aspectMode": "cover",
                    "action": {
                        "type": "uri",
                        "uri": resultList[1]
                    }
                },
            "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "action": {
                        "type": "uri",
                        "uri": resultList[1]
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": str + "で配信開始しました",
                            "size": "xxs",
                            "color": "#ff0000"
                        },
                        {
                            "type": "text",
                            "text": resultList[3],
                            "size": "xs"
                        },
                        {
                            "type": "text",
                            "text": resultList[0],
                            "size": "xl",
                            "weight": "bold"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": resultList[4],
                                            "size": "sm",
                                            "align": "start",
                                            "color": "#aaaaaa"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                    },
            "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#905c44",
                            "action": {
                                "type": "uri",
                                "label": "配信を見る",
                                "uri": resultList[1]
                            }
                        }
                    ]
            }
        }
    }

    obj = FlexSendMessage.new_from_json_dict(message)
    line_bot_api.broadcast(messages=obj)
    print("⭕配信中！通知しました：" + resultList[0])