#!/usr/bin/env python
# -*- coding: utf8 -*-

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


FRENCHMONTH={
	'01':'janvier',
	'02':'fevrier',
	'03':'mars',
	'04':'avril',
	'05':'mai',
	'06':'juin',
	'07':'juillet',
	'08':'aout',
	'09':'septembre',
	'10':'octobre',
	'11':'novembre',
	'12':'decembre',
	}
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
lastDay=(datetime.now()-timedelta(1)).strftime('%Y-%m-%dT00:00:00')
renass="http://renass.unistra.fr/\
fdsnws/event/1/query?orderby=time&format=json&longitude=1.9&limit=\
30&starttime=%s&latitude=46.6&maxradius=8.0" %lastDay
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

#utc to local, string format 2014-06-25T10:55:42
def utcToLocal(string):
	year=int(string[0:4])
	month=int(string[5:7])
	day=int(string[8:10])
	hour=int(string[11:13])
	minutes=int(string[14:16])
	sec=int(string[17:19])
	naive=datetime(year,month,day,hour,minutes,sec)
	local_dt=LOCAL.localize(naive, is_dst=None)
	utc_dt=local_dt.astimezone(UTC)
	string = utc_dt.strftime('%Y-%m-%dT%H:%M:%S')
	#print string
	return string


#time readable by humans
def conversion(string):
	year=int(string[0:4])
	month=int(string[5:7])
	day=int(string[8:10])
	hour=int(string[11:13])
	minutes=int(string[14:16])
	sec=int(string[17:19])
	naive=datetime(year,month,day,hour,minutes,sec,tzinfo=UTC)
	local_dt=naive.astimezone(LOCAL)
	string =local_dt.strftime('le %d %B %Y ')+u'à'+local_dt.strftime(' %H:%M:%S\
	 heure locale')
	return string 


#change time format : le 25 juin 2014 a 10:55:42 -> 2014-06-25T10:55:42
def reconversion(string):

	day=string[3:5]
	for key, value  in FRENCHMONTH.items():
		nbchar=string.find(value)
		if nbchar > 0 :
			month=key
			size=len(key)
			t=7+size
			year=string[t+2:t+6]
			hour=string[t+9:t+11]
			if hour < 10 :
				hour='0'+hour
			rest=string[t+12:t+17]
			string = year+u'-'+month+u'-'+day+u'T'+hour+u':'+rest
			#print 'avant conversion ', string
			string=utcToLocal(string)
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
	dcod=status[i].text
	informer = 1+dcod.find(u'\nle ')   
	#+ 1 because we begin at '\n' and not at 'l' char
	timesignal=u''
	if informer > 0 :
		while dcod[informer] != u'h' :
			timesignal = timesignal + dcod[informer]
			if informer < len(dcod)-1 :
				informer += 1
			else :
				break

	#timesignal = event dateof the last tweet put to the right format 
	timesignal=reconversion(timesignal)

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
	#year comparison 
	if int(time1[0:4]) > int(time2[0:4]) :
		rep=True
	elif int(time1[0:4]) < int(time2[0:4]) :
		rep=False
	else :
		#month comparison
		if int(time1[5:7]) > int(time2[5:7]) :
			rep=True
		elif int(time1[5:7]) < int(time2[5:7]) :
			rep=False
		else :
			#day comparison
			if int(time1[8:10]) > int(time2[8:10]) :
				rep=True
			elif int(time1[8:10]) < int(time2[8:10]) :
				rep=False
			else :
				#hour comparison
				if int(time1[11:13]) > int(time2[11:13]) :
					rep=True
				elif int(time1[11:13]) < int(time2[11:13]) :
					rep=False
				else :
					#min comparison
					if int(time1[14:16]) > int(time2[14:16]) :
						rep=True
					elif int(time1[14:16]) < int(time2[14:16]) :
						rep=False
					else :
						#sec comparison
						if int(time1[17:19]) > int(time2[17:19]) :
							rep=True
						elif int(time1[17:19]) < int(time2[17:19]) :
							rep=False
						else :
							#egality
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
	textJson= json.loads(text)

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