from twikit import Client, TooManyRequests
import time
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint
import os

MINIMUM_TWEETS = 10
QUERY = '(from:icardi) lang:tr until:2023-12-31 since:2023-01-01'


def get_tweets(tweets):
    if tweets is None:
        print(f'{datetime.now()} - Getting tweets...')
        tweets = client.search_tweet(QUERY, product='Top')
    else:
        wait_time = randint(5, 10)
        print(f'{datetime.now()} - Getting next tweets after {wait_time} seconds ...')
        time.sleep(wait_time)
        tweets = tweets.next()

    return tweets


# Konfigürasyonu yükle
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

# Client nesnesini oluşturma
client = Client(language='en-US')

# Eğer cookies.json yoksa oturum oluştur ve kaydet
if not os.path.exists('cookies.json'):
    print("cookies.json bulunamadı, oturum açılıyor ve kaydediliyor...")
    client.login(auth_info_1=username, auth_info_2=email, password=password)  # Login yap
    client.save_cookies('cookies.json')  # Oturumu cookies olarak kaydet
else:
    # Eğer cookies.json mevcutsa, bunu yükle
    print("cookies.json bulundu, load ediliyor...")
    client.load_cookies('cookies.json')

# CSV dosyası oluşturma
with open('tweets.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Tweet Count', 'Username', 'Text', 'Created At', 'Retweet Count', 'Like Count'])

tweet_count = 0
tweets = None

while tweet_count < MINIMUM_TWEETS:
    try:
        tweets = get_tweets(tweets)
    except TooManyRequests as e:
        rate_limit_reset = datetime.now() + timedelta(minutes=15)
        print(f'{datetime.now()} - Rate Limit Reached. Waiting Until {rate_limit_reset} ...')
        wait_time = rate_limit_reset - datetime.now()
        time.sleep(wait_time.total_seconds())
        continue

    if not tweets:
        print(f'{datetime.now()} - No more tweets.')
        break

    with open('tweets.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        for tweet in tweets:
            tweet_count += 1
            tweet_data = [
                tweet_count,
                getattr(tweet.user, 'name', ''),
                getattr(tweet, 'text', ''),
                getattr(tweet, 'created_at', ''),
                getattr(tweet, 'retweet_count', 0),
                getattr(tweet, 'favorite_count', 0)
            ]
            writer.writerow(tweet_data)

    print(f'{datetime.now()} - Got {tweet_count} tweets')

print(f'{datetime.now()} - Done! Got {tweet_count} tweets.')
