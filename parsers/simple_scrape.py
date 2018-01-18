# -*- coding: utf-8 -*-
#!/usr/bin/python

import sys
import redis
import string
import regex as re
import time
import twitter
from twitter_creds import TwitterApi
from api_check import check_api
from nyt import NYTParser

from nltk import bigrams

reload(sys)
sys.setdefaultencoding('utf8')

#from raven import Client
#client = Client('https://ad7b9867c209488da9baa4fbae04d8f0:b63c0acd29eb40269b52d3e6f82191d9@sentry.io/144998')

api = TwitterApi()

r = redis.StrictRedis(host='localhost', port=6379, db=0)


parser = NYTParser

def check_bigram(bigram, article_url, article_content):
    print('checking bigram (%s,%s)' % (bigram[0], bigram[1]))
    time.sleep(1)
    if not check_api(bigram):
        print('(%s,%s) not a unique bigram' % (bigram[0], bigram[1]))
        return
    #throttle tweets
    print('Found a unique bigram!! (%s,%s)' % (bigram[0], bigram[1]))
    if int(r.get("recently") or 0) < 4:
        r.incr("recently")
        r.expire("recently", 60 * 30)
        #tweet_bigram(bigram, article_url, article_content)


def tweet_bigram(bigram, article_url, article_content):
    try:
        tweet = ' '.join(bigram)
        status = api.PostUpdate(tweet)
    except UnicodeDecodeError:
        #client.captureException()
        pass
    except twitter.TwitterError:
        #client.captureException()
        pass


def ok_word(s):
    if s.endswith('.') or s.endswith('’'):  # trim trailing .
        s = s[:-1]
    
    if not s.islower() or s[0] is '@':
        return False

    return (not any(i.isdigit() or i == '.' or i == '@' or i == '/' or i == '#' for i in s))


def remove_punctuation(text):
    return re.sub(ur"’s", "", re.sub(ur"\p{P}+$", "", re.sub(ur"^\p{P}+", "", text)))


def normalize_punc(raw_word):
    #set various punctuation marks to hyphen to split on
    replaced_chars = [',', '—', '”', ':', '\'', '’s', '"']
    for char in replaced_chars:
        raw_word = raw_word.replace(char,'-')

    return raw_word.split('-')


def process_article(content, article):
    text = unicode(content)
    words = text.split()

    words = [normalize_punc(w) for w in words]
    flat_words = [w for wl in words for w in wl if w != '']

    for bigram in bigrams(flat_words):
        #check if both words are valid
        both_ok = True
        for word in bigram:
            if not ok_word(word):
                both_ok = False
        #check if the bigram already is in redis
        if both_ok:
            bigram = (remove_punctuation(bigram[0]), remove_punctuation(bigram[1]))
            wkey = "bigram:" + ','.join(bigram)
            if not r.get(wkey):
                check_bigram(bigram, article, text)
                r.set(wkey, '1')

def process_links(links):
    for link in links:
        akey = "article:" + link
        
        # unseen article
        if not r.get(akey): 
            time.sleep(1)
            parsed_article = parser(link)
            process_article(parsed_article, link)
            r.set(akey, '1')

def feed_urls_and_process():
    print("getting urls")
    links = list(set(parser.feed_urls()))
    print("processing urls")
    process_links(links)

feed_urls_and_process()
