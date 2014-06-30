require python-twitter and pytz module

execute  TOE.py 


necessary environment variable :
					CONSUMER_KEY=CgX2BuHNH29VlBBzyepCA2PG6
					CONSUMER_SECRET=utmpLerFVNkOV0ZC3CkGA8M3ND0akCa4TbSYCg5ekGx9GihCRQ
					ACCES_TOKEN_SECRET=rpZvwHJ5r2kMunt9dqaktbAG4JncMpTW0Z9oEduwb75Ma
					ACCES_TOKEN_KEY=2583918630-f4jNfYIKG34nY1lI1ffeh5gqWeSXxO4yVPooGgO


exit error :
 		 
 		 1 -> no environment value 
 		 2 -> wrong environment value for twitter (not working)


 working :

 	the programm looks for the last "good" tweet , ie the last earthquake published, catches the date and looks for every later event 
 	if the event is already published, it checks the associate url and detained from duplicate
 	if the last event published is not accessible for a special reason (too deep in the history , bug, ... )
 	it looks for the last tweet date and publish later event 

