

# import datetime

# def round_time(time, round_to, sign):

# 	rounded = time + datetime.timedelta(minutes=round_to/2.)
# 	rounded -= datetime.timedelta(minutes=rounded.minute % round_to,
# 									seconds=rounded.second,
# 									microseconds=rounded.microsecond)
# 	#dir is positive:
# 	if sign>0:
# 		if rounded>time:
# 			return rounded
# 		else: #rounded<time
# 			rounded+=datetime.timedelta(minutes=round_to)
# 			return rounded
# 	if sign<0:
# 		if rouounded
# 		else: #rounded<time
# 			return rounded




# time_in = datetime.datetime(2017,2,15,5,29,10)
# time_out = round_time(time_in, 15,-1)



import datetime
import dateutil.parser
import pprint 
from json import dumps
import simplejson, urllib



def get_travel_time(start_adr, stop_adr):

	url = "http://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN".format(str(start_adr),str(stop_adr))
	result= simplejson.load(urllib.urlopen(url))
	driving_time_sec = result['rows'][0]['elements'][0]['duration']['value']
	#print("Travel Time: %i sec")%(driving_time)

	#RETURN TRAVEL TIME IN MINUTES
	driving_time_min = driving_time_sec/60.0

	print driving_time_min
	return driving_time_min



get_travel_time('455 bay rd duxbury ma','455 bay rd duxbury ma')


# timestr = '2017-02-16T15:46:07-05:00'

# A = dateutil.parser.parse(timestr)
# print A
# hroff =  A.utcoffset().total_seconds()/3600
# b =datetime.datetime.now()
# print b-A
# b=b.isoformat()
# b= str(b)+'%i:00' %hroff
# B = dateutil.parser.parse(b)
# print B-A


# a = datetime.datetime(2017,2,16,10)
# b = datetime.datetime(2017,2,16,19)

# if a<b:
# 	print 'a is less than b'

# if a>b:
# 	print 'a is greater than b' 






