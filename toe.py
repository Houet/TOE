#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json
import twitter
import os 
import sys
import time
import pytz, datetime
from pytz import timezone
from datetime import datetime,timedelta
import locale
locale.setlocale(locale.LC_TIME,'')


YEAR={
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
UTC =pytz.utc

#url
magnitude=2.0
lastDay=(datetime.now()-timedelta(1)).strftime('%Y-%m-%dT00:00:00')
renass="http://renass.unistra.fr/\
fdsnws/event/1/query?orderby=time&format=json&longitude=1.9&minmagnitude=%s&\
limit=30&starttime=%s&latitude=46.6&maxradius=8.0" %(magnitude, lastDay)
print 'last day : ',lastDay

class MissingValue():
	""" exception raises when a value is missing  """

	def __init__(self,reason):
		self.reason=reason

	def __str__(self):
		return self.reason


class WrongValue():
	""" exception raises when a value is wrong """

	def __init__(self,reason):
		self.reason=reason

	def __str__(self):
		return self.reason


class NoData():
	"""exception raises when no JSON object could be decoded """

	def __init__(self,reason):
		self.reason=reason

	def __str__(self):
		return self.reason


#manage env var issue, help find missing values
def get_env_var(varname):
	variablename=os.getenv(varname)
	if not variablename :
		raise MissingValue("environment value not defined :%s" %varname)
	else :
		return variablename	

#manage bad authentification with twitter   :( doesnt work 
def Get_status(api,nb):
	statuses=api.GetHomeTimeline(count=nb)
	if not statuses:
		raise WrongValue("\nWrong values\n")
	else : 
		return statuses 


def Get_json(text):
	if text[0] != '{' :
		raise NoData("No data for your request")
	else :
		textJson=json.loads(text)
		return textJson

#time readable by humans
def conversion(string):
	utc_dt=datetime.strptime(string,'%Y-%m-%dT%H:%M:%S')
	naive= UTC.localize(utc_dt)
	local_dt=naive.astimezone(LOCAL)
	string =local_dt.strftime('le %d %B %Y ')+u'à'+local_dt.strftime(' %H:%M:%S\
	 heure locale')
	return string 


#change time format "twitter" to "normal" : 
#Thu Jun 26 07:40:58 +0000 2014 -> 2014-06-26T10:55:42
def convTimeTwitter(string):
	day=string[8:10]
	for key, value  in YEAR.items():
		nbchar=string.find(value)
		if nbchar > 0 :
			month=key
	year=string[26:30]
	hour=string[11:19]
	string=year+u'-'+month+u'-'+day+u'T'+hour
	return string


#the last "readable" tweet, event date recovery
def DateRecovery(status,data,size,i):
	response=None
	dcod=str(status[i])
	stringToFind='http://renass.unistra.fr/evenements/'
	informer=dcod.find(stringToFind)+len(stringToFind)
	Id = ''
	while dcod[informer] != '"' :
		Id = Id + dcod[informer]
		informer += 1

	#webservice data recovery
	if len(Id) > 15 :
		eventId="http://renass.unistra.fr/\
fdsnws/event/1/query?eventid=%s&format=json"%Id
		sock = urllib.urlopen(eventId)
		text = sock.read()
		sock.close()

	#data to json
		textJson= json.loads(text)

		timesignal=textJson['features'][0]['properties']['time']
	else :
		timesignal=Id

	#var to cover the list, possible= true if we find a "readable" tweet,
	# nb event since the last tweet "readable"
	t=0
	possible=True
	nbEvent=0

	#look for the last tweet 's time to limit data recovery
	while data['features'][t]['properties']['time'] != timesignal :
		nbEvent += 1
		if t < size-1 :
			t += 1
		else :  
			possible =False
			break

	if possible :
		response=nbEvent, conversion(timesignal)
	else :
		if i+1 < len(status):
			response=DateRecovery(status,data,size,i+1)
		else :
			#default response, no "readeble" tweet was found
			response =Default(status,data,size)
	return response


#recover the last tweet date, 
#even if its not a earthquake and recover all event from this date
def Default(status,data,size):
	print u'\nWe didn\'t find the last earthquake published\n\
	default recovery '
	time=convTimeTwitter(status[0].created_at)
	response=0,'none'
	#var to cover the list, possible= true if we find a "readable" tweet, 
	#nb event since the last tweet "readable"
	t=0
	possible=True
	nbEvent=0


	#look for the last tweet 's time to limit data recovery
	while compare(data['features'][t]['properties']['time'], time) :
		nbEvent += 1
		if t < size-1 :
			t += 1
		else :  
			possible =False
			break
	if possible :
		response=nbEvent, conversion(time)
	return response



#compare two date, return bool (== <=> false) 
#date format type 2014-06-26T10:55:42
def compare(time1,time2):
	rep=None
	times1=datetime.strptime(time1,'%Y-%m-%dT%H:%M:%S')
	times2=datetime.strptime(time2,'%Y-%m-%dT%H:%M:%S')
	duree= times1-times2
	if duree.total_seconds() > 0 :
		rep=True
	else :
		rep=False
	return rep



if __name__ == '__main__' :

	try :
		CONSUMER_KEY=get_env_var('CONSUMER_KEY')
		CONSUMER_SECRET=get_env_var('CONSUMER_SECRET')
		ACCES_TOKEN_KEY=get_env_var('ACCES_TOKEN_KEY')
		ACCES_TOKEN_SECRET=get_env_var('ACCES_TOKEN_SECRET')
	except MissingValue, e:
		print e
		sys.exit(1)

	#authentification
	api = twitter.Api(consumer_key=CONSUMER_KEY,consumer_secret=CONSUMER_SECRET,
	 access_token_key=ACCES_TOKEN_KEY, access_token_secret=ACCES_TOKEN_SECRET)
	
	

	#nb event to recovery
	nb=50

	#webservice data recovery
	sock = urllib.urlopen(renass)
	text = sock.read()
	sock.close()

	#data to json
	try :
		textJson=Get_json(text)
	except NoData, e:
		print e 
		sys.exit(3)

	#size of list
	size = len (textJson['features'])


	#tweet recovery
	try :
		statuses=Get_status(api,nb)
	except WrongValue,e :
		print e
		sys.exit(2) 

	#nb earthquake since last event published 
	nbEvent , date = DateRecovery(statuses,textJson,size,0)

	#if possible :
	print '\nLast event published: ',date,'\nNumber of event(s) \
	since :', nbEvent,'\n'


	#list of tweet aleady published, url comparison
	listOldEvent=[]
	for i in range(len(statuses)) :
		decodeMe=str(statuses[i])
		indication = decodeMe.find('http://renass.unistra.fr')
		link=''
		while decodeMe[indication] != '"' :
			link = link + decodeMe[indication]
			indication += 1
	 	listOldEvent.append(link)

	#print listOldEvent


	newTweet=0
	boule = True
	#tweet data + check if they are already published (compare url)
	for i in range(size-nbEvent,size):
		description=textJson['features'][size-1-i]['properties']['description']
		url=textJson['features'][size-1-i]['properties']['url']
		hour=textJson['features'][size-1-i]['properties']['time']
		hour=conversion((hour))

		for j in range(len (listOldEvent)):
			if url != listOldEvent[j] :
				boule = True
			else :
				print 'we already published this information !', listOldEvent[j]
				boule = False
				break

		if boule :		
			try :
				api.PostUpdate(description+"\n"+hour+"\n"+url)
				print 'Successful publication !\n', description 
				print hour , '\n', url
				newTweet += 1
			except :
				print "twitter : we already published this information !"

	if newTweet >= 1 :		
		print '\n',newTweet,'new tweet(s) were successfully published !!'	