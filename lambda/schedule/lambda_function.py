import requests
from datetime import datetime
from dateutil import tz
import pytz
import json
import sys, os

quadMap = {
    "quad1": 1,
    "quad2": 2,
    "quad3": 3,
    "quad4": 4
}

def convertDateTime(dateTime):
    from_zone = tz.gettz("Africa/Accra")
    to_zone = tz.gettz('America/New_York')
    test = dateTime
    test = test.split("T")[0] + " " + test.split("T")[1].split("Z")[0]
    utc = datetime.strptime(test, "%Y-%m-%d %H:%M")
    utc = utc.replace(tzinfo=from_zone)
    eastern = str(utc.astimezone(to_zone))
    date = eastern.split(" ")[0]
    time = eastern.split(" ")[1].split("-")[0]
    return date, time

def is_date_in_past(date_str):
    # Create a timezone object for Eastern Time
    eastern = pytz.timezone("US/Eastern")
    
    # Convert the date string to a datetime object
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Get the current date in Eastern Time
    now_eastern = datetime.now(eastern).date()
    
    # Return whether the given date is older than the current date
    return date < now_eastern

def call_espn_api(teamID, year):
    url = f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{teamID}/schedule'
    season_count = 2
    data = []
    while (season_count < 4):
        sports_response = requests.get(url,params={'season':year,'seasontype':str(season_count)})
        sports_json = sports_response.json()
        for game in sports_json['events']: 
            game_data = {}
            date,time = convertDateTime(game["date"])
            #date
            game_data['date'] = date
            #Change to date string
            game_data['dateString'] = date.replace('-', '')
            #time
            game_data['time'] = time
            #dateNumberString
            game_data['dateBox'] = date.replace("-","")
            #gameID
            game_data['gameId'] = game["id"]
            #neutralSite
            game_data['neutralSite'] = game['competitions'][0]["neutralSite"]
            #gameType
            try:
                game_data['gameType'] = game['competitions'][0]["type"]['abbreviation']
            except:
                game_data['gameType'] = 'POST'
            #completed
            game_data['completed'] = game['competitions'][0]['status']['type']['completed']
            #venue, score, opponentScore, opponentID, opponentName
            if game['competitions'][0]['competitors'][0]["id"] == teamID:
                if game_data['neutralSite']:
                    game_data['venue'] = "N"
                elif game['competitions'][0]['competitors'][0]["homeAway"] == "home":
                    game_data['venue'] = "H"
                else:
                    game_data['venue'] = "@"
                if game_data['completed']:
                    game_data['score'] = game['competitions'][0]['competitors'][0]["score"]['displayValue']
                    game_data['opponentScore'] = game['competitions'][0]['competitors'][1]["score"]['displayValue']
                game_data['opponentId'] = game['competitions'][0]['competitors'][1]["id"]
                game_data['opponentName'] = game['competitions'][0]['competitors'][1]['team']["displayName"]
                if game['competitions'][0]['competitors'][0]['homeAway'] == "home":
                    game_data['homeTeamId'] = teamID
                else:
                    game_data['homeTeamId'] = game['competitions'][0]['competitors'][1]["id"]
            else:
                if game_data['neutralSite']:
                    game_data['venue'] = "N"
                elif game['competitions'][0]['competitors'][0]["homeAway"] == "home":
                    game_data['venue'] = "@"
                else:
                    game_data['venue'] = "H"
                if game_data['completed']:
                    game_data['score'] = game['competitions'][0]['competitors'][1]["score"]['displayValue']
                    game_data['opponentScore'] = game['competitions'][0]['competitors'][0]["score"]['displayValue']
                game_data['opponentId'] = game['competitions'][0]['competitors'][0]["id"]
                game_data['opponentName'] = game['competitions'][0]['competitors'][0]["team"]["displayName"]
                if game['competitions'][0]['competitors'][0]['homeAway'] == "home":
                    game_data['homeTeamId'] = game['competitions'][0]['competitors'][0]["id"]
                else:
                    game_data['homeTeamId'] = teamID
            #result
            if game_data['completed']:
                if int(game_data['opponentScore']) > int(game_data['score']):
                    game_data['result'] = "L"
                elif int(game_data['opponentScore']) < int(game_data['score']):
                    game_data['result'] = "W"
                else:
                    game_data['result'] = None
            else:
                game_data['result'] = None

            #Add opponent data to data
            if is_date_in_past(game_data['date']) and game_data['completed'] == False:
                pass
            else:
                data.append(game_data)
        season_count += 1
    return data

def get_all_teams_data():
    url = "https://koric2.pythonanywhere.com/teamData"
    response = requests.request("GET", url).json()
    teamData = {}
    for team in response:
        teamData[team['id']] = team
    return teamData


def call_prediction_api(games):
    url = "https://koric2.pythonanywhere.com/predictList"

    payload = json.dumps({
    "games": games})
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()

def create_request_prediction_data(espnResponse,teamData):
    games = []
    for game in espnResponse:
        if not game['completed'] and game['opponentData'] != None:
            if game['venue'] == "@":
                games.append({
                    "homeData": game['opponentData']['average'],
                    "awayData": teamData['average'],
                    "neutralSite": game['neutralSite']
                    }
                )
            else:
                games.append({
                    "homeData": teamData['average'],
                    "awayData": game['opponentData']['average'],
                    "neutralSite": game['neutralSite']
                    }
                )
        
    return {
        "games": games
    }

def add_prediction_data(espnResponse,predictionResponse):
    predictionCount = 0
    for count,game in enumerate(espnResponse):
        if not game['completed'] and game['opponentData'] != None:
            if game['venue'] == "@":
                espnResponse[count]["scorePrediction"] = predictionResponse[predictionCount]['awayScore']
                espnResponse[count]["opponentScorePrediction"] = predictionResponse[predictionCount]['homeScore']
                espnResponse[count]["winProbability"] = 1 - predictionResponse[predictionCount]['prob']
            else:
                espnResponse[count]["scorePrediction"] = predictionResponse[predictionCount]['homeScore']
                espnResponse[count]["opponentScorePrediction"] = predictionResponse[predictionCount]['awayScore']
                espnResponse[count]["winProbability"] = predictionResponse[predictionCount]['prob']
            predictionCount += 1
        elif not game['completed']:
            espnResponse[count]["scorePrediction"] = None
            espnResponse[count]["opponentScorePrediction"] = None
            espnResponse[count]["winProbability"] = .99
    return espnResponse

def calculate_records(data):
    records = {
        "win" : 0,
        "loss": 0,
        "projectedWin":0,
        "projectedLoss":0,
        "confWin" : 0,
        "confLoss": 0,
        "confProjectedWin":0,
        "confProjectedLoss":0
    }
    probs = []
    for game in data:
        if game['completed']:
            if game['gameType'] == 'CONF':
                if game['result'] == 'W':
                    records['win'] += 1
                    records['confWin'] += 1
                if game['result'] == 'L':
                    records['loss'] += 1
                    records['confLoss'] += 1
            else:
                if game['result'] == 'W':
                    records['win'] += 1
                if game['result'] == 'L':
                    records['loss'] += 1
        else:
            probs.append((game['winProbability'], game['gameType'], game['opponentName'], game['opponentId']))
    wins,loss,confWin,confLoss = simulate(probs)
    records['projectedWin'] = wins + records['win']
    records['projectedLoss'] = loss + records['loss']
    records['confProjectedWin'] = confWin + records['confWin']
    records['confProjectedLoss'] = confLoss + records['confLoss']
    records['probs'] = probs
    return records

    

def quad_rank(opponent_rank,venue):
    if (opponent_rank <= 30 and venue == 'H') or (opponent_rank <= 50 and venue == 'N') or (opponent_rank <= 75 and venue == '@'):
        quad = "quad1"
    elif (opponent_rank <= 75 and venue == 'H') or (opponent_rank <= 100 and venue == 'N') or (opponent_rank <= 135 and venue == '@'):
        quad = "quad2"
    elif (opponent_rank <= 160 and venue == 'H') or (opponent_rank <= 200 and venue == 'N') or (opponent_rank <= 240 and venue == '@'):
        quad = "quad3"
    else:
        quad = "quad4"
    return quad
            
def calculate_quad_record(data,rank):
    quad_records = {
    "quad1": {'wins': 0, 'losses': 0},
    "quad2": {'wins': 0, 'losses': 0},
    "quad3": {'wins': 0, 'losses': 0},
    "quad4": {'wins': 0, 'losses': 0} 
    }
    for item in data:
        if item['completed']:
            #check if item has opponent data and ranks and rank
            if 'opponentData' in item and item['opponentData'] is not None:
                if 'ranks' in item['opponentData'] and item['opponentData']['ranks'] is not None:
                    if rank in item['opponentData']['ranks']:
                        opponent_rank = item['opponentData']["ranks"][rank]
                        venue = item["venue"]
                        quad = quad_rank(opponent_rank,venue)
                        if item['result'] == 'W':
                            quad_records[quad]['wins'] += 1
                        else:
                            quad_records[quad]['losses'] += 1
    return quad_records

def change_game_type(espnResponse, teamData):
    for count,game in enumerate(espnResponse):
        if espnResponse[count]['gameType'] == "POST":
            espnResponse[count]['gameType'] = "POST"

        elif espnResponse[count]['opponentData']:
            if teamData['conference'] == espnResponse[count]['opponentData'].get("conference"):
                espnResponse[count]['gameType'] = "CONF"
            else:
                espnResponse[count]['gameType'] = "REG"
        else:
            espnResponse[count]['gameType'] = "REG"
    return espnResponse

def simulate(probs):
    games = len(probs)
    wins = 0
    confGames = len(list(filter(lambda x: x[1] == "CONF", probs)))
    confWin = 0
    for prob in probs:
        if prob[3] != '-1':
            wins = prob[0] + wins
            if prob[1] == "CONF": 
                confWin = prob[0] + confWin
    wins = round(wins)
    loss = games - wins
    confWin = round(confWin)
    confLoss = confGames - confWin
    return wins,loss,confWin,confLoss


def add_odds(espnResponse):
    try:
        gameIDs = []
        for game in espnResponse:
            gameIDs.append(game['gameId'])
        
        url = "https://koric2.pythonanywhere.com/getOddsList"
        request =  {"gameIDs": gameIDs}
        payload = json.dumps(request)
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        odds = response.json()['games']
        oddsMap = {}
        for odd in odds:
            oddsMap[odd['gameID']] = {
                "spread": odd['spread'],
                "overUnder": odd['overUnder']
            }
        for count,game in enumerate(espnResponse):
            if game['gameId'] in oddsMap:
                espnResponse[count]['odds'] = oddsMap[game['gameId']]
            else:
                espnResponse[count]['odds'] = {
                "spread": None,
                "overUnder": None
            }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno, e)

    return espnResponse


def lambda_handler(event, context):
    try:
        teamID = event['teamID']
        year = event['year']
        netRank = event['netRank']

        teamsData = get_all_teams_data()
        espnResponse = call_espn_api(teamID, year)

        for count,game in enumerate(espnResponse):
            opponentData = teamsData[game['opponentId']] if game['opponentId'] in teamsData else None
            espnResponse[count]['opponentData'] = opponentData
            if opponentData != None:
                if netRank:
                    espnResponse[count]['quad'] = quadMap[quad_rank(opponentData['ranks']['net_rank'], game['venue'])]
                else:
                    espnResponse[count]['quad'] = quadMap[quad_rank(opponentData['ranks']['rank'], game['venue'])]

        requestPredictionData = create_request_prediction_data(espnResponse,teamsData[teamID])
        predictionResponse = call_prediction_api(requestPredictionData['games'])
        espnResponse = add_prediction_data(espnResponse,predictionResponse)
        espnResponse = change_game_type(espnResponse, teamsData[teamID])
        espnResponse = add_odds(espnResponse)
        records = calculate_records(espnResponse)
        if netRank:
            quad_records = calculate_quad_record(espnResponse,'net_rank')
        else:
            quad_records = calculate_quad_record(espnResponse,'rank')

        teamData = teamsData[teamID]['average']
        teamData['ranks']  = teamsData[teamID]['ranks']
        teamData['teamName'] = teamsData[teamID]['teamName']
        teamData['conference'] = teamsData[teamID]['conference']
        response = {
            "teamData": teamData,
            "games": espnResponse,
            "teamID": teamID,
            "year": year,
            "records": records,
            "quadRecords": quad_records,
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        response = {
            "error": str(e)
        }
    return response