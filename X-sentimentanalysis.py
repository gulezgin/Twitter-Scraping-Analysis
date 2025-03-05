import tweepy
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
import pandas as pd
import os
import matplotlib.pyplot as plt

nltk.download('vader_lexicon')

consumerKey = "r39YngJy6XMEWKamZkR7DWeQO"
consumerSecret = "jQ4pzqhUVUcUvMttq9k5XoBTTcmZJKzIcknBiieSh2isBCFOPh"
accessToken = "1375422736667934724-FxhZsFBIlzpV0EwnBYJsSG1d9EAXF4"
accessTokenSecret = "YIzKpTMR3mt5i41at6ROmdO7WBSGZh5xLMGuIn8KwpoY9"

auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)
api = tweepy.API(auth)


def percentage(part, whole):
    return 100 * float(part) / float(whole)


keyword = input("Hesap Adı veya Hashtag giriniz:")
noOfTweet = int(input("Tweet sayısı giriniz:"))
tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang="tr", tweet_mode="extended").items(noOfTweet)

positive = 0
negative = 0
neutral = 0

tweet_list = []
neutral_list = []
positive_list = []
negative_list = []

for tweet in tweets:
    print(tweet.full_text)
    tweet_list.append(tweet.full_text)
    analysis = TextBlob(tweet.full_text)
    score = SentimentIntensityAnalyzer().polarity_scores(tweet.full_text)
    neg = score['neg']
    neu = score['neu']
    pos = score['pos']

    if neg > pos:
        negative_list.append(tweet.full_text)
        negative += 1
    elif pos > neg:
        positive_list.append(tweet.full_text)
        positive += 1
    else:
        neutral_list.append(tweet.full_text)
        neutral += 1

positive = percentage(positive, noOfTweet)
negative = percentage(negative, noOfTweet)
neutral = percentage(neutral, noOfTweet)

labels = ["Positive [" + str("{:.1f}".format(positive)) + "%]",
          "Neutral [" + str("{:.1f}".format(neutral)) + "%]",
          "Negative [" + str("{:.1f}".format(negative)) + "%]"]
sizes = [positive, neutral, negative]
colors = ["yellowgreen", "blue", "red"]

plt.pie(sizes, colors=colors, startangle=90)
plt.legend(labels)
plt.axis("equal")
plt.title("Duygu Analizi: " + keyword)
plt.show()
