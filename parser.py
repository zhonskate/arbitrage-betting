from pathlib import Path
import json
import requests
import os

REGIONS = 'eu' # uk | us | eu | au. Multiple can be specified if comma delimited
MARKETS = 'h2h' # h2h | spreads | totals. Multiple can be specified if comma delimited
ODDS_FORMAT = 'decimal' # decimal | american
DATE_FORMAT = 'iso' # iso | unix

# 0 show arbitrable matches above threshold
# 1 show all arbitrable matches
# 2 show optimal odds for all matches
# 3 show warnings and relevant msgs for debug
# 4 show all messages and data including json dumps
VERBOSITY = 0

# Percentage of guaranteed win
THRESHOLD = 2

# Amount willing to bet in total
BET_SIZE = 100


JSON_PATH = Path(__file__).parent / "jsons"
API_KEY_PATH = Path(__file__).parent / "key.txt"

def pretty_print(msg: str, level: int):
    if level <= VERBOSITY:
        print(msg) 

def create_path_if_not_exists():
    if not JSON_PATH.exists():
        os.mkdir(JSON_PATH)

def get_api_key():
    with open(API_KEY_PATH, 'r') as f:
        return f.read().strip()


def get_sports_list(key: str) -> dict:
    sports_response = requests.get('https://api.the-odds-api.com/v4/sports', params={
        'api_key': key
    })

    if sports_response.status_code != 200:
        pretty_print(f'Failed to get sports: status_code {sports_response.status_code}, response body {sports_response.text}', 3)
    
    with open(JSON_PATH / "sports.json", 'w') as f:
        json.dump(sports_response.json(), f)
    
    return sports_response.json()


def write_sport_json(sport: str, key: str) -> None:
    sport_path = JSON_PATH / f"{sport}.json"
    
    if sport_path.is_file():
        pretty_print(f"{sport} file already exists. Remove it if you want to refresh.", 3)
        return
    
    
    odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/odds', params={
        'api_key': key,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
    })

    if odds_response.status_code != 200:
        pretty_print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}', 3)

    else:
        odds_json = odds_response.json()
        pretty_print(f'Number of events: {len(odds_json)}', 4)
        pretty_print(odds_json, 4)
        
        with open(JSON_PATH / f"{sport}.json", 'w') as f:
            json.dump(odds_json, f)

        # Check the usage quota
        pretty_print(f"Remaining requests {odds_response.headers['x-requests-remaining']}", 3)
        pretty_print(f"Used requests {odds_response.headers['x-requests-used']}", 3)


def process_match(match: dict) -> dict:
    pretty_print(f"[[[{match['home_team']} VS {match['away_team']}]]]", 2)
    
    bookmakers = match['bookmakers']
    
    if not bookmakers:
        return []
    
    results = [
        {"platform": "undefined", "price": 0.0} 
        for outcome in bookmakers[0]['markets'][0]['outcomes']
    ]
    
    for bookmaker in bookmakers:
        platform = bookmaker['title']
        outcomes = bookmaker['markets'][0]['outcomes']
        if len(outcomes) != len(results):
            continue
        
        for i in range(len(outcomes)):
            if outcomes[i]['price'] > results[i]["price"]:
                results[i]["price"] = outcomes[i]['price']
                results[i]["platform"] = platform
        
        printer = f"{bookmaker['title']} - "
        for outcome in outcomes:
            printer += f"{outcome['name']}[{outcome['price']}] "
        
        pretty_print(printer, 4)
    
    return results


def is_arbitrable(data:dict):
    total_sum = 0.0
    for outcome in data:
        value = 1/outcome['price']
        total_sum += value
    
    if total_sum < 1:
        return True
    return False


def get_margin(data: dict):
    total_sum = 0.0
    for outcome in data:
        value = 1/outcome['price']
        total_sum += value
    
    margin = 1-total_sum
    return round(margin*100,2)

def get_rates(data: dict, verbosity: int, bet_size: float = 100.0):
    total_sum = 0.0
    for outcome in data:
        value = 1/outcome['price']
        total_sum += value
    
    margin = 1-total_sum
    pretty_print(f"earnings = {round(margin*100,2)}%  [{round(bet_size*margin,2)}]\n", verbosity)
    
    complete_sum = 0.0
    for outcome in data:
        price = outcome['price']
        percentage = 1/price/total_sum
        value = round(1/price + margin*percentage, 4)
        outcome_bet_size = round(bet_size*value, 2)
        gross_gain = round(outcome_bet_size*price, 2)
        net_gain = round(gross_gain - bet_size, 2)
        pretty_print(f"{round(value*100,2)}% [{outcome_bet_size} * {price} = {gross_gain}] -> {net_gain}", verbosity)
        complete_sum += value
    pretty_print("--------------------\n", verbosity)
    
    pretty_print(f"\n{round(complete_sum,2)}\n", 4)


def process_sport(sport: str) -> None:
    sport_path = JSON_PATH / f"{sport}.json"
    
    if not sport_path.is_file():
        return
    
    with open(sport_path) as file:
        parsed_file = json.load(file)
        
        for match in parsed_file:
            results = process_match(match)
            if not results:
                continue
            pretty_print(f"{results}", 2)
            if is_arbitrable(results):
                margin = get_margin(results)
                verbosity = 0 if margin >= THRESHOLD else 1
                if VERBOSITY < 2:
                    pretty_print(f"[[[{match['home_team']} VS {match['away_team']}]]]", verbosity)
                    pretty_print(f"{results}", verbosity)
                
                pretty_print("--------\nARBITRABLE\n--------", verbosity)
                get_rates(results, verbosity, BET_SIZE)
            pretty_print("\n", 2)
    



if __name__ == "__main__":
    create_path_if_not_exists()
    
    key = get_api_key()
    
    sports_list = [sport["key"] for sport in get_sports_list(key)]
    
    for sport in sports_list:
        write_sport_json(sport, key)
        process_sport(sport)
