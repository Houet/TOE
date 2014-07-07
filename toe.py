#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" read README.txt """

import urllib
import json
import twitter
import os
import sys
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

URL_ARG = {
    "orderby"     : "time",
    "format"      : "json",
    "longitude"   : "1.9",
    "latitude"    : "46.6",
    "limit"       : "30",
    "maxradius"   : "8.0",
    "starttime"   : (datetime.now()-timedelta(2)).strftime('%Y-%m-%dT00:00:00'),
    "minmagnitude": "2.0",
    }

#timezone
LOCAL = timezone("Europe/Paris")
UTC = pytz.utc

URL_BASE = "http://renass.unistra.fr/"
URL_SEARCH = "fdsnws/event/1/query?"
URL_FIND = "evenements/"


class MissingValue(Exception):
    """ exception raises when a value is missing  """

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


class WrongValue(Exception):
    """ exception raises when a value is wrong """

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


class NoData(Exception):
    """exception raises when no JSON object could be decoded """

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


def get_env_var(varname):
    """ manage env var issue, help find missing values """
    variablename = os.getenv(varname)
    if not variablename:
        raise MissingValue("environment value not defined : %s" %varname)
    else:
        return variablename


def get_status(twitter_api, number_of_tweet):
    """ manage bad authentification with twitter """
    try:
        twitter_status = twitter_api.GetHomeTimeline(count=number_of_tweet)
    except:
        raise WrongValue("Wrong identification for twitter")

    return twitter_status


def get_json(text_to_convert):
    """ manage error when loading to json """
    if text_to_convert[0] != '{':
        raise NoData("No data for your request")
    else:
        text_to_json = json.loads(text_to_convert)
        return text_to_json


def try_get(varname):
    """ not choose yet """
    try:
        ret = get_env_var(varname)
    except MissingValue:
        logging.warning('no value for environment variable %s,\
 default = 2', varname)
        ret = 2
    return ret


def conversion(string):
    """ time readable by humans """
    utc_dt = datetime.strptime(string, '%Y-%m-%dT%H:%M:%S')
    naive = UTC.localize(utc_dt)
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
    string = year + u'-' + month + u'-' + day + u'T' + hour
    return string


def date_recovery(status, data, list_size, status_number):
    """ the last "readable" tweet, event date recovery """
    dcod = str(status[status_number])
    informer = dcod.find(URL_BASE + URL_FIND) + len(URL_BASE + URL_FIND)
    event_id = ''
    while dcod[informer] != '"':
        event_id = event_id + dcod[informer]
        informer += 1

    #webservice data recovery
    if len(event_id) > 15:
        URL_ARG['eventid'] = event_id
        url_id = URL_BASE + URL_SEARCH + urllib.urlencode(URL_ARG.items())

    #data to json
        try:
            have_json = get_json(urllib.urlopen(url_id).read())
            urllib.urlopen(url_id).close()
            timesignal = have_json['features'][0]['properties']['time']
        except NoData:
            logging.info(NoData)
            timesignal = event_id


    else:
        timesignal = event_id

    #var to cover the list, possible= true if we find a "readable" tweet,
    # nb event since the last tweet "readable"
    num = 0
    possible = True
    nb_event = 0

    #look for the last tweet 's time to limit data recovery
    while data['features'][num]['properties']['time'] != timesignal:
        nb_event += 1
        if num < list_size - 1:
            num += 1
        else:
            possible = False
            break

    if possible:
        response = nb_event, conversion(timesignal)
    else:
        if status_number + 1 < len(status):
            response = date_recovery(status, data, list_size, status_number + 1)
        else:
            #default response, no "readable" tweet was found
            response = default(status, data, list_size)
    return response


def default(status, data, size_of_list):
    """ recover the last tweet date,
    even if its not a earthquake and recover all event from this date
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
    date format type 2014-06-26T10:55:42"""
    rep = None
    times1 = datetime.strptime(time1, '%Y-%m-%dT%H:%M:%S')
    times2 = datetime.strptime(time2, '%Y-%m-%dT%H:%M:%S')
    duree = times1 - times2
    if duree.total_seconds() > 0:
        rep = True
    else:
        rep = False
    return rep


def function_logging(arg_sys):
    """MODULE LOGGING"""
    if len(arg_sys) == 2:
        loglevel = str(arg_sys[1])
    else:
        loglevel = 'warning'

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
    except MissingValue:
        logging.error(MissingValue)
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
    """ list of tweet aleady published, url comparison """

    #list of tweet aleady published, url comparison
    list_old_event = []
    for i in range(len(status)):
        decode_me = str(status[i])
        indication = decode_me.find(URL_BASE)
        link = ''
        while decode_me[indication] != '"':
            link = link + decode_me[indication]
            indication += 1
        list_old_event.append(link)
    return list_old_event


def main(argv=None):
    """ fonction main """
    if argv is None:
        argv = sys.argv

    function_logging(argv)

    api = twitter.Api(**env())

    last_day = (datetime.now() - timedelta(int(try_get('NB_DAY')))).strftime('\
%Y-%m-%dT00:00:00')

    # get env var, by default magnitude = 2 and dday = 2
    URL_ARG['starttime'] = last_day
    URL_ARG['minmagnitude'] = try_get('MAGNITUDE_MIN')
    renass = URL_BASE + URL_SEARCH + urllib.urlencode(URL_ARG.items())


    #webservice data recovery
    sock = urllib.urlopen(renass)

    #data to json
    try:
        text_json = get_json(sock.read())
        sock.close()
    except NoData:
        logging.info(NoData)
        sys.exit(3)

    #size of list
    size = len(text_json['features'])


    #tweet recovery , number of tweet we want to recover
    try:
        statuses = get_status(api, 50)
    except WrongValue:
        logging.error(WrongValue)
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
    sys.exit(main())
