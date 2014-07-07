#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" read README.txt """

import urllib
import json
import twitter
import os
import sys
import time
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

    def __str__(self):
        return self.reason


class WrongValue(Exception):
    """ exception raises when a value is wrong """

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason

    def __str__(self):
        return self.reason


class NoData(Exception):
    """exception raises when no JSON object could be decoded """

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason

    def __str__(self):
        return self.reason


def get_env_var(varname):
    """ manage env var issue, help find missing values """
    variablename = os.getenv(varname)
    if not variablename:
        raise MissingValue("environment value not defined : %s" %varname)
    else:
        return variablename


def get_status(API, nb):
    """ manage bad authentification with twitter """
    try:
        statuses = API.GetHomeTimeline(count=nb)
    except:
        raise WrongValue("\nWrong identification for twitter\n")

    return statuses


def get_json(text):
    """ manage error when loading to json """
    if text[0] != '{':
        raise NoData("No data for your request")
    else:
        textJson = json.loads(text)
        return textJson


def try_get(varname):
    """ not choose yet """
    try:
        ret = get_env_var(varname)
    except: 
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
        Thu Jun 26 07:40:58 +0000 2014 -> 2014-06-26T10:55:42 """
    day = string[8:10]
    for key, value  in YEAR.items():
        nbchar = string.find(value)
        if nbchar > 0:
            month = key
    year = string[26:30]
    hour = string[11:19]
    string = year + u'-' + month + u'-' + day + u'T' + hour
    return string


def date_recovery(status, data, size, i):
    """ the last "readable" tweet, event date recovery """
    response = None
    dcod = str(status[i])
    stringToFind = URL_BASE + URL_FIND
    informer = dcod.find(stringToFind) + len(stringToFind)
    Id = ''
    while dcod[informer] != '"':
        Id = Id + dcod[informer]
        informer += 1

    #webservice data recovery
    if len(Id) > 15:
        URL_ARG['eventid'] = Id
        eventId = URL_BASE + URL_SEARCH + urllib.urlencode(URL_ARG.items())
        sock = urllib.urlopen(eventId)
        text = sock.read()
        sock.close()

    #data to json
        try:
            textJson = get_json(text)
            timesignal = textJson['features'][0]['properties']['time']
        except NoData, e:
            logging.info(e)
            timesignal = Id


    else:
        timesignal = Id

    #var to cover the list, possible= true if we find a "readable" tweet,
    # nb event since the last tweet "readable"
    t = 0
    possible = True
    nbEvent = 0

    #look for the last tweet 's time to limit data recovery
    while data['features'][t]['properties']['time'] != timesignal:
        nbEvent += 1
        if t < size - 1:
            t += 1
        else:
            possible = False
            break

    if possible:
        response = nbEvent, conversion(timesignal)
    else:
        if i + 1 < len(status):
            response = date_recovery(status, data, size, i + 1)
        else:
            #default response, no "readable" tweet was found
            response = default(status, data, size)
    return response


def default(status, data, size):
    """ recover the last tweet date,
    even if its not a earthquake and recover all event from this date """
    logging.info(u"We didn't find the last earthquake published :\
    default recovery ")
    time = conv_time_twitter(status[0].created_at)
    response = 0, 'none'
    #var to cover the list, possible= true if we find a "readable" tweet, 
    #nb event since the last tweet "readable"
    t = 0
    possible = True
    nbEvent = 0


    #look for the last tweet 's time to limit data recovery
    while compare(data['features'][t]['properties']['time'], time):
        nbEvent += 1
        if t < size-1:
            t += 1
        else:
            possible = False
            break
    if possible:
        response = nbEvent, conversion(time)
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



if __name__ == '__main__':


    #MODULE LOGGING
    if len(sys.argv) == 2:
        loglevel = str(sys.argv[1])
    else:
        loglevel = 'warning'

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    formatter = '%(asctime)s :: %(levelname)s :: %(message)s'
    logging.basicConfig(level=numeric_level, format=formatter)


    try:
        CONSUMER_KEY = get_env_var('CONSUMER_KEY')
        CONSUMER_SECRET = get_env_var('CONSUMER_SECRET')
        ACCES_TOKEN_KEY = get_env_var('ACCES_TOKEN_KEY')
        ACCES_TOKEN_SECRET = get_env_var('ACCES_TOKEN_SECRET')
    except MissingValue, e:
        logging.error(e)
        sys.exit(1)

    #authentification

    key_dict = {
        'consumer_key'       : CONSUMER_KEY,
        'consumer_secret'    : CONSUMER_SECRET,
        'access_token_key'   : ACCES_TOKEN_KEY,
        'access_token_secret': ACCES_TOKEN_SECRET,
    }

    API = twitter.Api(**key_dict)



    #nb event to recovery
    nb = 50

    # get env var, by default magnitude = 2 and dday = 2
    magnitude = try_get('MAGNITUDE_MIN')
    dday = try_get('NB_DAY')

    lastDay = (datetime.now() - timedelta(int(dday))).strftime('%Y-%m-%dT00:00:00')

    URL_ARG['starttime'] = lastDay
    URL_ARG['minmagnitude'] = magnitude
    renass = URL_BASE + URL_SEARCH + urllib.urlencode(URL_ARG.items())


    #webservice data recovery
    sock = urllib.urlopen(renass)
    text = sock.read()
    sock.close()

    #data to json
    try:
        textJson = get_json(text)
    except NoData, e:
        logging.info(e)
        sys.exit(3)

    #size of list
    size = len(textJson['features'])


    #tweet recovery
    try:
        statuses = get_status(API, nb)
    except WrongValue, e:
        logging.error(e)
        sys.exit(2)

    #nb earthquake since last event published
    nbEvent, date = date_recovery(statuses, textJson, size, 0)

    #if possible :
    logging.info('\nLast event published: %s \nNumber of event(s) \
    since :%s \n', date, nbEvent)


    #list of tweet aleady published, url comparison
    listOldEvent = []
    for i in range(len(statuses)):
        decodeMe = str(statuses[i])
        indication = decodeMe.find(URL_BASE)
        link = ''
        while decodeMe[indication] != '"':
            link = link + decodeMe[indication]
            indication += 1
        listOldEvent.append(link)


    newTweet = 0
    #tweet data + check if they are already published (compare url)
    for i in range(size - nbEvent, size):
        description = textJson['features'][size - 1 - i]['properties']['description']
        url = textJson['features'][size - 1 - i]['properties']['url']
        time = textJson['features'][size - 1 - i]['properties']['time']
        time = conversion(time)

        if not url in listOldEvent:
            try:
                API.PostUpdate(description + "\n" + time + "\n" + url)
                logging.info('Successful publication ! %s', description)
                logging.info('%s %s', time, url)
                newTweet += 1
            except:
                logging.warning("twitter: information was already published !")

    if newTweet >= 1:
        logging.info('%s new tweet(s) were successfully published!!', newTweet)
