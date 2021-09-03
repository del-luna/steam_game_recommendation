import time
import json
import random
import requests
from tqdm import tqdm
import pandas as pd
from bs4 import BeautifulSoup

'''
Workspace : Colab
It takes about 2 Hours 22 minutes to collect 300 reviews for each 10000 games.
get_n_appids(n=10000) takes about 15 minutes
more details in steam api 'reference' section in the readme.md 

'''

def get_n_reviews(appid, n=300):
    '''
    Latest game reviews like Hades are not loaded.
    '''
    global reviews
    start = time.time()
    cursor = '*'
    params = {
            'json' : 1,
            'filter' : 'all',
            'language' : 'korean', #if you want english replace the parameter with 'english'.
            'day_range' : 9223372036854775807,
            'review_type' : 'all',
            'purchase_type' : 'all'
            }


    params['cursor'] = cursor.encode()
    params['num_per_page'] = 100
    
    while len(reviews) < n:
        url = 'https://store.steampowered.com/appreviews/'
        response = requests.get(url=url+str(appid), params=params, headers={'User-Agent': 'Mozilla/5.0'}).json()
        reviews += response['reviews']
        if len(response['reviews']) < 100:
            break
        params['cursor'] = response['cursor'].encode()
        time.sleep(random.random()+1) # for Max retries error

def get_n_appids(n=1000, mode='all'):
    '''
    mode = all, topselleres, etc..
    if mode == all : About 100K games can be viewd
    if mode == topsellers : only 3K games can be viewed
    
    '''
    appids = []
    if mode == 'all':
        url = f'https://store.steampowered.com/search/?&page='
    if mode == 'topselleres':
        url = f'https://store.steampowered.com/search/?category1=998&filter={mode}&page='
    page = 1
    
    while page*25 < n:
        start = time.time()
        page += 1
        response = requests.get(url=url+str(page), headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all(class_='search_result_row'):
            try:
                app_id = int(row['data-ds-appid'])
                #If the game has dlc, multiple lists are created here
            except ValueError:
                app_id = int(row['data-ds-appid'][0])
            except KeyError:
                app_id = int(json.loads(row['data-ds-bundle-data'])['m_rgItems'][0]['m_rgIncludedAppIDs'][0])
            appids.append(app_id)
        
        time.sleep(random.random()+1) # for Max retries error
        
        if page==2:
            print(f'only one loop spending time :{time.time()-start}')
        
    return appids[:n]

if __name__ == '__main__':
    
    #It takes about 24 minutes to load a list of 10K games.
    app_ids = get_n_appids(n=10000)

    reviews = []
    user_ids = []
    game_ids = []
    num_games = []
    num_reviews = []
    play_times = []
    ratings = []
    vote_conf = []
    weights = []
    game_reviews = []


    for game_id in tqdm(app_ids[:3000]):
        get_n_reviews(game_id) #make reviews
        
        #print(f'Complete {i}th game review collection')
        
        if len(reviews) == 0:
            continue
        
        #start = time.time()
        for idx in range(len(reviews)):
            user_ids.append(reviews[idx]['author']['steamid'])
            game_ids.append(game_id)
            try:
                play_times.append(reviews[idx]['author']['playtime_at_review'])
            except KeyError:
                '''
                many game reivews have no 'playtime_at_review' property
                in this caes replace playtime_at_review -> playtime_forever
                '''
                play_times.append(reviews[idx]['author']['playtime_forever'])
            num_games.append(reviews[idx]['author']['num_games_owned'])
            num_reviews.append(reviews[idx]['author']['num_reviews'])
            ratings.append(1 if reviews[idx]['voted_up'] else 0)
            vote_conf.append(int(reviews[idx]['votes_up']) + int(reviews[idx]['votes_funny']))
            weights.append(reviews[idx]['weighted_vote_score'])
            game_reviews.append(reviews[idx]['review'])
        
        reviews = [] #global variable initialization
        #print(f'inner loop spending time : {time.time()-start}')
    
    steam_ratings = pd.DataFrame({'user_ids':user_ids,
                              'game_ids':game_ids,
                              'num_games_owned':num_games,
                              'num_reviews':num_reviews,
                              'play_times':play_times,
                              'ratings':ratings,
                              'vote_conf':vote_conf,
                              'weights':weights,
                              'game_reviews':game_reviews})
    steam_ratings.to_csv('ratings.csv', encoding='utf-8-sig')