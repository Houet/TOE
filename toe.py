#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" read README.txt """

import urllib
import json
import twitter
import os
import logging
import pytz
import time
import datetime
from pytz import timezone
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_TIME, '')

#timezone
LOCAL = timezone("Europe/Paris")

URL_SEARCH = "http://renass.unistra.fr/fdsnws/event/1/query?"
URL_FILTER = "http://renass.unistra.fr/evenements"

class MissingValue(Exception):
    """ exception raises when a value is missing  """
    pass


def get_env_var(varname, default=None):
    """ manage env var issue, help find missing values """
    value = os.getenv(varname, default)

    if not value:
        raise MissingValue("environment value not defined : %s" %varname)

    return value


def conversion(string):
    """ time readable by humans """
    utc_dt = datetime.strptime(string, '%Y-%m-%dT%H:%M:%S')
    naive = pytz.utc.localize(utc_dt)
    local_dt = naive.astimezone(LOCAL)
    string = local_dt.strftime('le %d %B %Y ') + u'à' + local_dt.strftime(' %H:%M:%S heure locale')
    return string


def GetApi():
    """ get the api twitter """

    try:
        consumer_key = get_env_var('CONSUMER_KEY')
        consumer_secret = get_env_var('CONSUMER_SECRET')
        acces_token_key = get_env_var('ACCES_TOKEN_KEY')
        acces_token_secret = get_env_var('ACCES_TOKEN_SECRET')
    except MissingValue, exception:
        logging.error(exception)
        sys.exit(1)

    #authentification

    key_dict = {
        'consumer_key'       : consumer_key,
        'consumer_secret'    : consumer_secret,
        'access_token_key'   : acces_token_key,
        'access_token_secret': acces_token_secret,
    }

    return twitter.Api(**key_dict)


def GetTwitterTimeline():
    """ Get the twitter timeline """

    api = GetApi()

    try:
        Timeline = api.GetHomeTimeline(count=150)
    except twitter.TwitterError, exception:
        logging.error(exception)
        sys.exit(2)

    return Timeline


def ReadJson(url):
    """ recover data from webservice in format json """
    print url
    sock = urllib.urlopen(url)
    try:
        data_json = json.load(sock)
        sock.close()
    except ValueError:
        logging.error("decoding Json has failed")
        sys.exit(3)

    return data_json


def GetStartimeFromTwitter():
    """ get the date of the last earthquake published """
    twitter_timeline = GetTwitterTimeline()
    list_url = [t.urls[0].expanded_url for t in twitter_timeline if t.urls]
    filtered_list = [u for u in list_url if URL_FILTER in u]

    try:
        url_argv = {
            'eventid': filtered_list[0].split('/')[-1],
            'format' : 'json',
        }
    except IndexError:
        logging.info("no earthquake found on twitter")
        date_post = time.gmtime(twitter_timeline[0].created_at_in_seconds)
        return time.strftime('%Y-%m-%dT%H:%M:%S', date_post)
    else:
        url_id = URL_SEARCH + urllib.urlencode(url_argv.items())
        startime_twit = ReadJson(url_id)['features'][0]['properties']['time']
        return startime_twit


def GetStarttimeFromYesterday():
    """get yesterday's date  """

    nb_day = get_env_var("NB_DAY", 1)
    yesterday = datetime.now() - timedelta(nb_day)
    return yesterday


def GetMostRecentStartime():
    """get the most recent startime """
    date_yesterday = GetStarttimeFromYesterday()
    date_twitter = datetime.strptime(GetStartimeFromTwitter(), '%Y-%m-%dT%H:%M:%S') + timedelta(0, 1)
    if date_yesterday > date_twitter:
        return date_yesterday
    else:
        return date_twitter


def GetDataToPublish():
    """ get data to publish """
    starttime = GetMostRecentStartime().strftime('%Y-%m-%dT%H:%M:%S')
    minmagnitude = get_env_var("MAGNITUDE_MIN", 2)

    url_arg = {
        "orderby"     : "time",
        "format"      : "json",
        "longitude"   : "1.9",
        "latitude"    : "46.6",
        "limit"       : "30",
        "maxradius"   : "8.0",
        "starttime"   : starttime,
        "minmagnitude": minmagnitude,
    }

    webservice = URL_SEARCH + urllib.urlencode(url_arg.items())
    data_recovered = ReadJson(webservice)

    return data_recovered


def Publish():
    """ publish data """

    api = GetApi()
    data = GetDataToPublish()

    url = [u['properties']['url'] for u in data['features']]
    date = [t['properties']['time'] for t in data['features']]
    date = map(conversion, date)
    description = [d['properties']['description'] for d in data['features']]

    lat = [l['geometry']['coordinates'][1] for l in data['features']]
    lon = [l['geometry']['coordinates'][0] for l in data['features']]

    message = zip(description, date, url, lat, lon)
    message.reverse()

    for mes in message:
        try:
            api.PostUpdate('\n'.join(mes[0:3]), latitude=mes[3], longitude=mes[4])
        except twitter.TwitterError, exception:
            logging.error(exception)
            sys.exit(2)


if __name__ == '__main__':
    import sys
    import argparse

    Publish()
