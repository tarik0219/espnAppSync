import requests
import json

def get_odds(gameID):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{gameID}/competitions/{gameID}/odds?="
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()

def change_odds_response(response):
    sportsbooks = []
    for sportsbook in response['items']:
        name = sportsbook['provider']['name']
        spread = sportsbook['spread']
        overUnder = sportsbook['overUnder']
        sportsbooks.append(
            {
                'sportsbook': name,
                'spread': spread,
                'overUnder': overUnder
            }
        )
    return sportsbooks

def get_boxscore(gameID):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={gameID}"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()

def change_boxscore_response(response):
    for count,teams in enumerate(response['boxscore']['teams']):
        if count == 0:
            awayTeam = teams['team']['displayName']
        else:
            homeTeam = teams['team']['displayName']
            break

    return homeTeam, awayTeam

def combine_responses(gameID):
    odds = get_odds(gameID)
    boxscore = get_boxscore(gameID)
    homeTeam, awayTeam = change_boxscore_response(boxscore)
    sportsbooks = change_odds_response(odds)
    return {
        "awayTeam": awayTeam,
        "homeTeam": homeTeam,
        "sportsbooks": sportsbooks
    }


def lambda_handler(event, context):
    print("event",event)
    try:
        # Extract data from the AppSync input event
        gameId = event['gameID']
        responseBody = combine_responses(gameId)
        print(responseBody)
        return responseBody

    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": str(e),
            "headers": {
                "Content-Type": "text/plain"
            }
        }