#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" read README.txt """

import urllib
import json
import twitter
import os
import logging
import pytz
import datetime
from pytz import timezone
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_TIME, '')


YEAR = {
    '01':'Jan',
    '02':'Feb',
    '03':'Mar',
    '04':'Apr',
    '05':'May',
    '06':'Jun',
    '07':'Jul',
    '08':'Aug',
    '09':'Sep',
    '10':'Oct',
    '11':'Nov',
    '12':'Dec',
    }


#timezone
LOCAL = timezone("Europe/Paris")

URL_BASE = "http://renass.unistra.fr/"
URL_SEARCH = "fdsnws/event/1/query?"
URL_FIND = "evenements/"


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
    string = local_dt.strftime('le %d %B %Y ') + u'à' + local_dt.strftime(' \
%H:%M:%S heure locale')
    return string


def conv_time_twitter(string):
    """ change time format "twitter" to "normal" :
        Thu Jun 26 07:40:58 +0000 2014 -> 2014-06-26T10:55:42
    """
    day = string[8:10]
    for key, value  in YEAR.items():
        nbchar = string.find(value)
        if nbchar > 0:
            month = key
    year = string[26:30]
    hour = string[11:19]
    string = year + '-' + month + '-' + day + 'T' + hour
    return string


def date_recovery(status, data, list_size, status_number):
    """ the last "readable" tweet, event date recovery """

    try:
        event_id = status[status_number].urls[0].expanded_url[36:60]
    except IndexError:
        return date_recovery(status, data, list_size, status_number + 1)

    #webservice data recovery
    url_argv = {
        'eventid' : event_id,
        'format' : 'json',
    }

    url_id = URL_BASE + URL_SEARCH + urllib.urlencode(url_argv.items())

    #data to json
    try:
        have_json = json.loads(urllib.urlopen(url_id).read())
        urllib.urlopen(url_id).close()
        timesignal = have_json['features'][0]['properties']['time']
    except ValueError:
        logging.info("decoding Json has failed")
        timesignal = event_id

    #var to cover the list, possible= true if we find a "readable" tweet,
    # nb event since the last tweet "readable"
    num = 0
    possible = True
    number_event = 0

    #look for the last tweet 's time to limit data recovery
    while data['features'][num]['properties']['time'] != timesignal:
        number_event += 1
        if num < list_size - 1:
            num += 1
        else:
            possible = False
            break

    if possible:
        response = number_event, conversion(timesignal)
    else:
        if status_number + 1 < len(status):
            response = date_recovery(status, data, list_size, status_number + 1)
        else:
            #default response, no "readable" tweet was found
            response = default(status, data, list_size)
    return response


def default(status, data, size_of_list):
    """ recover the last tweet date,
    even if its not a earthquake and recover all later event
    """

    logging.info("We didn't find the last earthquake published :\
    default recovery ")
    tim_2_comp = conv_time_twitter(status[0].created_at)
    response = 0, 'none'
    #var to cover the list, possible= true if we find a "readable" tweet,
    #nb event since the last tweet "readable"
    loop_var = 0
    possible = True
    number_of_event = 0


    #look for the last tweet 's time to limit data recovery
    while compare(data['features'][loop_var]['properties']['time'], tim_2_comp):
        number_of_event += 1
        if loop_var < size_of_list-1:
            loop_var += 1
        else:
            possible = False
            break
    if possible:
        response = number_of_event, conversion(tim_2_comp)
    return response


def compare(time1, time2):
    """ compare two date, return bool (== <=> false)
    date format type 2014-06-26T10:55:42
    """
    times1 = datetime.strptime(time1, '%Y-%m-%dT%H:%M:%S')
    times2 = datetime.strptime(time2, '%Y-%m-%dT%H:%M:%S')
    duree = times1 - times2
    if duree.total_seconds() > 0:
        return True
    else:
        return False


def function_logging(arg_sys):
    """MODULE LOGGING"""

    loglevel = arg_sys

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    formatter = '%(asctime)s :: %(levelname)s :: %(message)s'
    logging.basicConfig(level=numeric_level, format=formatter)
    return


def env():
    """recuperation of environment variables """
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
    return key_dict


def recup_old_event(status):
    """ list of url from tweet aleady published """

    list_old_event = []
    for i in range(len(status)):
        try:
            list_old_event.append(status[i].urls[0].expanded_url)
        except IndexError:
            continue
    return list_old_event


def main(argv="warning"):
    """ fonction main """

    function_logging(argv)

    api = twitter.Api(**env())

    url_arg = {
        "orderby"     : "time",
        "format"      : "json",
        "longitude"   : "1.9",
        "latitude"    : "46.6",
        "limit"       : "30",
        "maxradius"   : "8.0",
        "starttime"   : (datetime.now()-timedelta(2)).strftime('\
%Y-%m-%dT00:00:00'),
        "minmagnitude": "2.0",
    }


    last_day = (datetime.now() - timedelta(int(get_env_var('\
NB_DAY', default=2)))).strftime('%Y-%m-%dT00:00:00')

    # get env var, by default magnitude = 2 and dday = 2
    url_arg['starttime'] = last_day
    url_arg['minmagnitude'] = get_env_var('MAGNITUDE_MIN', default=2)
    renass = URL_BASE + URL_SEARCH + urllib.urlencode(url_arg.items())

    #webservice data recovery
    sock = urllib.urlopen(renass)

    #data to json
    try:
        text_json = json.loads(sock.read())
        sock.close()
    except ValueError:
        logging.error("decoding Json has failed")
        sys.exit(3)

    #size of list
    size = len(text_json['features'])


    #tweet recovery , number of tweet we want to recover
    try:
        statuses = api.GetHomeTimeline(count=150)
    except twitter.TwitterError, exception:
        logging.error(exception)
        sys.exit(2)

    #nb earthquake since last event published
    num_event, date = date_recovery(statuses, text_json, size, 0)

    #if possible :
    logging.info('Last event published: %s Number of event(s) \
since :%s', date, num_event)

    new_tweet = 0
    tweet_data = {}
    #tweet data + check if they are already published (compare url)
    for i in range(size - num_event, size):

        tweet_data['description'] = text_json['features'][size - 1 - i]['\
properties']['description']
        tweet_data['url'] = text_json['features'][size - 1 - i]['\
properties']['url']
        tweet_data['age'] = conversion(text_json['features'][size - 1 - i]['\
properties']['time'])
        tweet_data['lat'] = text_json['features'][size - 1 - i]['\
geometry']['coordinates'][1]
        tweet_data['lon'] = text_json['features'][size - 1 - i]['\
geometry']['coordinates'][0]

        if not tweet_data['url'] in recup_old_event(statuses):
            try:
                api.PostUpdate(tweet_data['description'] + "\n" + tweet_data['\
age'] + "\n" + tweet_data['url'], latitude=tweet_data['\
lat'], longitude=tweet_data['lon'])
                logging.info('\
Successful publication ! %s', tweet_data['description'])
                logging.info('%s %s', tweet_data['age'], tweet_data['url'])
                new_tweet += 1
            except Warning:
                logging.warning("twitter: information was already published !")

    if new_tweet >= 1:
        logging.info('%s new tweet(s) were successfully published!!', new_tweet)


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Tweet earthquake')
    parser.add_argument('-l', metavar='lvl', help='logging level')

    args = parser.parse_args()
    if args.l:
        sys.exit(main(argv=args.l))
    else:
        sys.exit(main())
