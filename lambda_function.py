import main
import boto3
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):

    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('junRemind')
    response = table.scan()
    oldLiveTime = response["Items"][0]['liveTime']

    result = main.twitchMain(oldLiveTime)

    if result is not None:
        table.update_item(
            Key={'liveTime': result[3]}
        )

    return 'success'