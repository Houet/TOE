#!/usr/bin/env python
# -*- coding=utf-8 -*-
""" read README.txt """

import urllib
import json
import os
import sys
import logging
import time
import pytz
from twitter import Twitter, OAuth, TwitterError
from pytz import timezone
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_TIME, '')


LOCAL = timezone("Europe/Paris")

URL_SEARCH = "http://renass.unistra.fr/fdsnws/event/1/query?"
URL_FILTER = "http://renass.unistra.fr/evenements"


class MissingValue(Exception):
    """ exception raises when a value is missing  """
    pass


class TweetEvent():
    """ """
    def __init__(self, geojson):
        """ """
        self.description = geojson["properties"]["description"]
        self.url = geojson["properties"]["url"]
        self.date = conversion(geojson["properties"]["time"])

        self.lat = geojson["geometry"]["coordinates"][1]
        self.lon = geojson["geometry"]["coordinates"][0]

    def unicode(self):
        """ """
        return


def get_env_var(varname, default=None):
    """ manage env var issue, help find missing values """
    value = os.getenv(varname, default)

    if not value:
        raise MissingValue("environment value not defined : %s" % varname)

    return value


def conversion(string):
    """ time readable by humans """
    utc_dt = datetime.strptime(string, '%Y-%m-%dT%H:%M:%S')
    naive = pytz.utc.localize(utc_dt)
    local_dt = naive.astimezone(LOCAL)
    string = local_dt.strftime('le %d %B %Y à %H:%M:%S heure locale')
    return string


def get_twitter_timeline():
    """ Get the twitter timeline """

    try:
        timeline = api.statuses.home_timeline(count=150)
    except TwitterError as exception:
        logging.error(exception)
        sys.exit(2)

    return timeline


def read_json(url):
    """ recover data from webservice in format json """
    logging.info(url)
    try:
        sock = urllib.request.urlopen(url)
        sock = sock.read()
    except urllib.error.HTTPError:
        logging.warning("decoding Json has failed")
        sys.exit(3)
    else:
        data_json = json.loads(bytes.decode(sock))
        return data_json


def get_startime_from_twitter():
    """ get the date of the last earthquake published """
    twitter_timeline = get_twitter_timeline()
    list_url = [t['entities']['urls'][0]['expanded_url'] for
                t in twitter_timeline if t['entities']['urls']]
    filtered_list = [u for u in list_url if URL_FILTER in u]
    logging.debug('list of event: %s', filtered_list)
    try:
        url_argv = {
            'eventid': filtered_list[0].split('/')[-1],
            'format': 'json',
        }
    except IndexError:
        logging.info("no earthquake found on twitter")
        date_post = time.gmtime(twitter_timeline[0].created_at_in_seconds)
        return time.strftime('%Y-%m-%dT%H:%M:%S', date_post)
    else:
        url_id = URL_SEARCH + urllib.parse.urlencode(url_argv)
        logging.info('url of the last earthquake published :')
        startime_twit = read_json(url_id)['features'][0]['properties']['time']
        return startime_twit


def get_starttime_from_yesterday():
    """get yesterday's date  """

    nb_day = int(get_env_var("NB_DAY", 1))
    yesterday = datetime.now() - timedelta(nb_day)
    return yesterday


def get_most_recent_starttime():
    """get the most recent startime """
    date_yesterday = get_starttime_from_yesterday()
    logging.info('start time from user: %s', date_yesterday)

    date_twitter = datetime.strptime(get_startime_from_twitter(),
                                     '%Y-%m-%dT%H:%M:%S') + timedelta(0, 1)
    logging.info('start time from twitter: %s', date_twitter)

    return max(date_twitter, date_yesterday)


def get_data_to_publish():
    """ get data to publish """
    starttime = get_most_recent_starttime().strftime('%Y-%m-%dT%H:%M:%S')
    logging.info("most recent start time : %s", starttime)
    minmagnitude = get_env_var("MAGNITUDE_MIN", 2)

    url_arg = {
        "orderby": "time",
        "format": "json",
        "longitude": "1.9",
        "latitude": "46.6",
        "limit": "30",
        "maxradius": "8.0",
        "starttime": starttime,
        "minmagnitude": minmagnitude,
    }

    webservice = URL_SEARCH + urllib.parse.urlencode(url_arg)
    logging.info("url of data we recovered")
    data_recovered = read_json(webservice)

    return data_recovered


def formatting():
    """ preformating tweet in order to publish them """

    data = get_data_to_publish()

    url = [u['properties']['url'] for u in data['features']]
    date = [t['properties']['time'] for t in data['features']]
    date = map(conversion, date)
    description = [d['properties']['description'] for d in data['features']]

    lat = [l['geometry']['coordinates'][1] for l in data['features']]
    lon = [l['geometry']['coordinates'][0] for l in data['features']]

    message = list(zip(description, date, url, lat, lon))
    message.reverse()
    logging.info("data to publish: %s", message)

    for mes in message:
        publish('\n'.join(mes[0:3]), mes[3], mes[4])


def publish(tweet, latitude=None, longitude=None):
    """ publish data on twitter"""

    try:
        api.statuses.update(status=tweet, lat=latitude,
                            long=longitude)
    except TwitterError as exception:
        logging.error(exception)
        sys.exit(2)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(
        description="publish earthquake on twitter")

    parser.add_argument("-l", "--loglevel", help="change the logging level",
                        default="error",
                        choices=['debug', 'info', 'warning', 'error'])
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    form = '%(levelname)s :: %(asctime)s :: %(message)s'
    logging.basicConfig(level=numeric_level, format=form)

    # authentification
    try:
        api = Twitter(auth=OAuth(get_env_var('ACCES_TOKEN_KEY'),
                                 get_env_var('ACCES_TOKEN_SECRET'),
                                 get_env_var('CONSUMER_KEY'),
                                 get_env_var('CONSUMER_SECRET')))
    except MissingValue as exception:
        logging.error(exception)
        sys.exit(1)

    formatting()
