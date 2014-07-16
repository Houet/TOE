#TOE



### What is TOE ?

*****************


TOE is an application which publishes on twitter earthquakes from 
http://renass.unistra.fr/ using the Twitter API



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

error and information could be found in status_logging.txt


### Working :

*************


The programm looks for the last "good" tweet ,ie the last earthquake published, 
catches the date and looks for every later event .
If the event has already been published, it checks the associate url and 
detaines from duplicating; 
if the last event published is not accessible 
for a special reason (too deep in the history , bug, ... )
it looks for the last tweet date and publishes later event.

All earthquake published should respect a minimun magnitude and are not older 
than one day when they are published. These parameters can be changed with 
the MAGNITUDE_MIN and NB_DAY environment values.


### Necessary  :

****************


Following environment variables are necessary :					
* CONSUMER_KEY
* CONSUMER_SECRET
* ACCES_TOKEN_SECRET
* ACCES_TOKEN_KEY


### Exit error :
 
****************		 
 

|	Code    |   		  Description			   |
|-----------|--------------------------------------|
|	  1     |  No environment value                |
|	  2     |  Wrong environment value for twitter | 
|	  3     |  No json could be decoded            |







