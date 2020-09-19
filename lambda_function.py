import main

def lambda_handler(event, context):
    main.twitchMain()
    return 'success'