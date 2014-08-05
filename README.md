#TOE



### What is TOE ?

*****************


TOE is an application which publishes on twitter earthquakes from 
http://renass.unistra.fr/ using the Twitter API



### How to use it ?

*******************


Install with:

```
git clone https://github.com/Houet/Toe.git
sudo apt-get install pytz
sudo apt-get install twitter
```

Then run in the appropriate directory:

```
./toe.py 
```

See help:
```
./toe.py -h
```

Change log level with adding "-l":
```
./toe.py -l debug
```

Change tweet format with adding "-f" and choose between 0, 1 or 2:
```
./toe.py -f 1
```


### Working:

************


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

It includes a environment value SEUIL_TEMOIGNAGE which changes the output tweet
when magnitude is higher than this value with adding a encouragement to
testifie. Default value is 5.2 ML.


### Necessary:

**************


Following environment variables are necessary :					
* CONSUMER_KEY
* CONSUMER_SECRET
* ACCES_TOKEN_SECRET
* ACCES_TOKEN_KEY


### Exit error:
 
***************		 
 

|	Code    |   		  Description			   |
|-----------|--------------------------------------|
|	  1     |  No environment value                |
|	  2     |  Wrong environment value for twitter | 
|	  3     |  Invalid url                         |







