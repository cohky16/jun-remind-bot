import main

def lambda_hundler(event, context):
    main.twitchMain()
    return 'success'