from itertools import product
from twikit import Client, TooManyRequests
import time
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint
from twikitscrapev2 import tweet_data

MINIMUM_TWEETS = 100
QUERY = 'icardi'

#login credentials
config = ConfigParser ()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

print(f"Username: {username}, Email: {email}, Password: {password}")

# create a csv file
with open('tweetsm.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow('Tweet Count', 'Username', 'Text', 'Created At', 'Retweets', 'Likes')

#authenticate to X.com
#client = Client(language='en-US')
client = Client()
#client.login(auth_info_1=username, auth_info_2=email, password=password)
#client.save_cookies('cookies.json')

client.load_cookies('cookies.json')

tweet_count = 0
tweets = None

while tweet_count < MINIMUM_TWEETS:
    if tweets is None:
        #get tweet
        print(f'{datetime.now()} - Getting tweets..')
        tweets = client.search_tweet(QUERY, product='Top')
    else:
        print(f'{datetime.now()} - Getting next tweets')
        tweets = tweets.next()

    if not tweets:
        print(f'{datetime.now()} - No more tweets found')
        break

    for tweet in tweets:
        tweet_count += 1
        tweets_data = [tweet_count, tweet.user.name, tweet.text, tweet.created_at, tweet.retweet_count, tweet.favorite_count]

        with open ('tweetsm.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(tweet_data)

    print(f'{datetime.now()} - Got {tweet_count} tweets')

print(f'{datetime.now()} - Done! Got {tweet_count} tweets found')