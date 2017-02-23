from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask.ext.cors import CORS, cross_origin
from sqlalchemy import create_engine
from json import dumps
import simplejson, urllib

#from __future__ import print_function
import httplib2
import os
import datetime
import dateutil.parser

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from calendar_io_obj import Calendar_IO 

ERROR = 999

print '\n=== Remark Scheduler ===\n\n'


#This is needed for the Google API...
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

#Create a engine for connecting to SQLite3.
#Assuming salaries.db is in your app root folder
#e = create_engine('sqlite:///salaries.db')



def getDateTimeFromISO(s):
    d = dateutil.parser.parse(s)
    return d


def pull_calendar_openings(Calendar, photographer, address, start_date_str, end_date_str, appt_time, time_offset, base_price):
	'''
	Inputs:
	Calendar: Calendar_IO Object
	photographer: String of the photographers name. Thas has to match up with the calendar object's list of emails
	start_date: String of time in iso format. This is when the query should start
	end_date: String of time in iso format. This is when the query should end
	'''

	global ERROR

	#Make sure you are talking about a valid photographer
	if photographer not in Calendar.photographer_ids:
		print "No photographer found"
		return ERROR

	date_now = datetime.datetime.utcnow()
	start_date = getDateTimeFromISO(start_date_str)
	end_date = getDateTimeFromISO(end_date_str)#-datetime.timedelta(0,1)

	#Checks against the date you are trying to pull
	if (start_date-date_now).total_seconds < (-6*12*3600):
		print "Pulling Too Far In Past"
		start_date=date_now
		end_date = start_date+datetime.timedelta(7)


	all_events = Calendar.get_calendar_openings_with_travel(photographer,address,start_date,end_date,appt_time,time_offset,base_price)
	
	try:
		1+1
	except Exception as e:
		print 'Error Calling Calendar.get_calendar_openings_with_travel'
		print e
		all_events=ERROR

	return all_events
	
def add_appointment(Calendar, photographer, agent, address, start, end, phone_n, products, details, title):
	'''
	This function calls the Calendar object to add an appointment. 
	Add any pre-checks here
	'''
	global ERROR

	if photographer not in Calendar.photographer_ids:
		print "Photographer not found"
		return None

	start = getDateTimeFromISO(start)
	end = getDateTimeFromISO(end)

	event = Calendar.create_appointment(photographer, agent, address, start, end, phone_n, products, details, title)

	return event


###########################################################################################################
################################# START OF API ROUTING ####################################################
###########################################################################################################


Calendar = Calendar_IO(flags)

app = Flask(__name__)
api = Api(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def index():
    return "MAGA: Make API's Great Again! Time: %s" %datetime.datetime.utcnow().isoformat()



@app.route('/_pull_events', methods=['GET','POST'])
@cross_origin()
def pull_events():

	global ERROR
	global Calendar

	data = request.get_json()
	

	time_now = datetime.datetime.utcnow().isoformat()
	time_p_7 = (datetime.datetime.utcnow()+datetime.timedelta(7)).isoformat()

	agent = data.get('agent','None')				#request.args.get('agent', 'None', type=str)
	photographers = data.get('photog','None')		#request.args.get('photog', 'None', type=str)
	address = data.get('address','None')			#request.args.get('address', 'Boston,MA', type=str)
	start =	data.get('start',time_now)				#request.args.get('start', time_now, type=str)
	end = data.get('end',time_p_7)					#request.args.get('end', time_p_7, type=str)
	appt_time = data.get('appt_time',60)			#request.args.get('appt_time', 60, type=int)
	time_offset = data.get('time_offset',300)
	base_price = data.get('base_price',99)

	#print appt_time
	print 'Pulling Agent: %s' %agent


	events_output = []
	for photographer in photographers:

		events = pull_calendar_openings(Calendar, photographer, address, start, end, appt_time,time_offset,base_price)
		try:
			#events = pull_calendar_openings(Calendar, photographer, address, start, end, appt_time,time_offset,base_price)
			print 'Num: %i' %len(events)
		except Exception as e:
			events = ERROR
			print 'Error in pull_events: ',e

		if events == ERROR:
			print 'ERROR in /_pull_events'
			break
		
		events_output += events




	return jsonify(result =events_output)


@app.route('/_make_appointment', methods=['GET','POST'])
@cross_origin()
def make_appointment():

	data = request.get_json()
	print 'Creating Appointment Function'
	print data
	global Calendar

	# Check to see if this appointment already exists, if so, update it. 
	time_now = datetime.datetime.utcnow().isoformat()
	
	title = data.get('title','None')
	agent = data.get('agent','None') 				#request.args.get('agent', 'None', type=str)
	photographer = data.get('photog','None')		#request.args.get('photog', 'None', type=str)
	address = data.get('address','None')			#request.args.get('address', 'Boston,MA', type=str)
	start = data.get('start',None)				#request.args.get('start', time_now, type=str)
	end = data.get('end',None)
	#appt_time = data.get('appt_time',60) 			#request.args.get('appt_time', 60, type=int)
	phone_n = data.get('phone_n','None')
	products = data.get('products',['None Indicated'])
	details = data.get('details',['None Indicated'])

	#try:
	appt = add_appointment(Calendar, photographer, agent, address, start, end, phone_n, products, details, title)
	# except Exception as e:
	# 	print "Error Creating Appointment."
	# 	print e
	# 	appt = 999

	return jsonify(result = appt)


if __name__ == '__main__':
    app.run(debug=True)





