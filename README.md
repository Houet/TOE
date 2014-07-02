#TOE



### What is TOE ?

*****************


TOE is an application which published on twitter earthquakes from 
http://renass.unistra.fr/



### How to use it ?  :

**********************


Add the two modules python-twitter and pytz :

```
sudo apt-get install python-twitter 
sudo apt-get install pytz
```

then run in the appropriate directory :

```
python toe.py 
```


### working :

*************


The programm looks for the last "good" tweet ,ie the last earthquake published, 
catches the date and looks for every later event .
If the event is already published, it checks the associate url and 
detained from duplicate; 
if the last event published is not accessible 
for a special reason (too deep in the history , bug, ... )
it looks for the last tweet date and publish later event.

All earthquake published should respect a minimun magnitude and are not older 
than 2 days when they are published. This parameters can be change with 
the MAGNITUDE_MIN and NB_DAY environment values.


### necessary environment variable :

************************************

					
* CONSUMER_KEY
* CONSUMER_SECRET
* ACCES_TOKEN_SECRET
* ACCES_TOKEN_KEY


### exit error :
 
****************		 
 

|	Code    |   		  Description			   |
|-----------|--------------------------------------|
|	  1     |  No environment value                |
|	  2     |  Wrong environment value for twitter | 
|	  3     |  No json could be decode             |







