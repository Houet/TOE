### require :

python-twitter and pytz module

execute  toe.py 

### necessary environment variable :
					
* CONSUMER_KEY
* CONSUMER_SECRET
* ACCES_TOKEN_SECRET
* ACCES_TOKEN_KEY


### exit error :
 		 
- 1 -> no environment value 
- 2 -> wrong environment value for twitter 
- 3 -> No json could be decode 


### working :

The programm looks for the last "good" tweet ,ie the last earthquake published, 
catches the date and looks for every later event .
If the event is already published, it checks the associate url and 
detained from duplicate; 
if the last event published is not accessible 
for a special reason (too deep in the history , bug, ... )
it looks for the last tweet date and publish later event.

All earthquake published should respect a minimun magnitude and are not older 
than 2 days. This parameters can be change with the MAGNITUDE_MIN and NB_DAY
environment values.

