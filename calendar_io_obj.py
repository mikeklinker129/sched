#from __future__ import print_function
import httplib2
import os
from json import dumps
import simplejson, urllib
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import sys

import datetime
import dateutil

class Calendar_IO():
		# If modifying these scopes, delete your previously saved credentials
	# at ~/.credentials/calendar-python-quickstart.json
	

	def __init__(self,flags):
		self._CLIENT_SECRET_FILE = 'client_secret.json'
		self._SCOPES = 'https://www.googleapis.com/auth/calendar'
		self._APPLICATION_NAME = 'Google Calendar API Python'
		self._flags = flags
		self.ERROR = 999

		self.photographer_ids = {
			'primary':'primary',
			'Mike Klinker Main':'mikeklinker129@gmail.com',
			'Mike Klinker Aux':'4cbk355kbcifkf56mo7nancqns@group.calendar.google.com',
			'alex':'alex@remarkvisions.com',
		}

		self.work_hours = [8,6+12]

		self.current_events = None

		self.credentials = self.setup_credentials()
		self.service = self.setup_service()
		print 'Initialized Google Calendar IO'


	def calc_cost(self,event):
		print event
		# ['costFactor'] = iterN, travel to, travel from
		cost1 = 0
		cost2 = 0
		cost3 = 0
		fac1 = event['costFactor'][0]
		fac2 = event['costFactor'][1]
		fac3 = event['costFactor'][2]

		if fac1>0:
			cost1 = 50

		time_thres = 30
		cost_per_min = 1.5 #dollars per minute over time_thres of travel
		if fac2>time_thres:
			cost2 = (fac2-time_thres)*cost_per_min
		if fac3>time_thres:
			cost3 = (fac3-time_thres)*cost_per_min

		price = event['cost_est'] + cost1+cost2+cost3

		return int(price) #'%i, %i, %i' %(cost1,cost2,cost3)




	def get_calendar_openings_with_travel(self, photographer,address,start_date,end_date, appt_time, time_offset, base_price):

		events = []
		events = self.get_calendar_events_with_travel(photographer,address,start_date,end_date, appt_time)
		
		try:
			events.sort(key=lambda r: r['start'])
		except Exception as e:
			print e


		# print '\n\n\n'
		# for i in events:
		# 	print 'Event: %s' %(i['title'])
		# print '\n\n\n'

		if events==self.ERROR:
			return self.ERROR
		 #create a start time and stop time (6am til 8pm) for a given day
 		 #March through all events on that day, see whats avail.


 		if len(events)>1:
 			try:
	 			g_cal_time_offset = -dateutil.parser.parse(str(events[0]['start'])).utcoffset().total_seconds()/60
 				if g_cal_time_offset!=time_offset:
 					print 'Discrepency Between Google Calendar Timezone and Javascript'
				time_offset=g_cal_time_offset
			except Exception as e:
				print e


 		#start in the morning on the start_date
 		#see if the appt will fit
 		start_work_hr = int(self.work_hours[0])#+time_offset/60)
 		stop_work_hr = int(self.work_hours[1])#+time_offset/60)
 		start_date_local = start_date + datetime.timedelta(0,time_offset*60)#Dont use this for time computations.

 		current_time = datetime.datetime.utcnow().isoformat()+'-%i:00' %int(time_offset/60)
 		current_time = dateutil.parser.parse(current_time)
 		current_time = current_time - datetime.timedelta(0,time_offset*60)
 		
 		for event in events:
			time_s = dateutil.parser.parse(str(event['start']))
 			time_e = dateutil.parser.parse(str(event['end']))
 			if time_s.utcoffset()==None:
 				event['start'] = time_s.isoformat()+'-%i:00' %int(time_offset/60)
 			if time_e.utcoffset()==None:
 				event['end'] = time_e.isoformat()+'-%i:00' %int(time_offset/60)	

 		all_free_time = []
 		for i in range(0,(end_date-start_date).days):
 			#This is now a loop through every day within your query period
	 		delta_day = datetime.timedelta(i)
	 		start_work_day= datetime.datetime(start_date_local.year,start_date_local.month,start_date_local.day,start_work_hr)+delta_day
	 		start_work_str = start_work_day.isoformat()+'-%i:00' %int(time_offset/60)
	 		start_work_day = dateutil.parser.parse(start_work_str)
	 		stop_work_day = start_work_day+datetime.timedelta(0, (self.work_hours[1]-self.work_hours[0])*3600 )

	 		
	 		if start_work_day.weekday()>4:
	 			#print 'Current Day: ',start_work_day.isoformat(),'. Weekend, Continuing'
	 			continue
	 		else:
	 			1+1
	 			#print 'Current Day: ',start_work_day.isoformat(),' day of week: %i' %start_work_day.weekday()

	 		if current_time>start_work_day and current_time<stop_work_day:
	 			start_work_day = current_time+datetime.timedelta(0,3600)
	 		elif current_time>stop_work_day:
	 			continue

	 		#These are now the major bounds for starting and stopping work on a given day. 
	 		temp_day_events = []
	 		allday_event = 0
	 		for event in events:
	 			time_s = dateutil.parser.parse(str(event['start']))
	 			time_e = dateutil.parser.parse(str(event['end']))


	 			if time_s.day==start_work_day.day:
	 				if time_e>start_work_day and time_s<stop_work_day:
	 					temp_day_events.append(event) #List of the events on our given day within working hours
	 					if time_s<start_work_day and time_e>stop_work_day:
	 						allday_event+=1

	 		if allday_event>0:
	 			continue

	 		if start_work_day>stop_work_day:
	 			continue

	 		free_time = []
	 		#If the day is empty, make the full day empty. 
	 		if len(temp_day_events)==0:
	 			e = self.create_free_time_slot(start_work_day,stop_work_day)
	 			#print e['start'], e['end']
	 			free_time.append(e)
	 			all_free_time+=free_time
	 			continue

	 		if len(temp_day_events)==1:
	 			time0 = dateutil.parser.parse(temp_day_events[0]['end'])
	 			time1 = dateutil.parser.parse(temp_day_events[0]['start'])
	 			time_between_min0 = (stop_work_day - time0).total_seconds()/60
	 			time_between_min1 = (time1 - start_work_day).total_seconds()/60
	 			if time_between_min0>=appt_time:
 					e = self.create_free_time_slot(time0,stop_work_day)
 					free_time.append(e)
 				if time_between_min1>=appt_time:
 					e = self.create_free_time_slot(start_work_day,time1)
 					free_time.append(e)


	 		#If there are events on this day, lets find the open slots. 
	 		for i in range(0,len(temp_day_events)-1):
	 			event1 = temp_day_events[i]
	 			event2 = temp_day_events[i+1]
	 			
	 			trav_to = 0
	 			trav_from = 0

	 			time1s = dateutil.parser.parse(str(event1['start']))
	 			
	 			if i==0:
	 				#print 'Initial Got Called Because i=%i' %i
	 				time1s = dateutil.parser.parse(str(event1['start']))
	 				time_between_min = (time1s - start_work_day).total_seconds()/60
	 				if time_between_min >= appt_time:
	 					if event1['type']=='travel_block':
	 						trav_from = event1['length_min']
	 					e = self.create_free_time_slot(start_work_day,time1s,trav_to,trav_from)
	 					free_time.append(e)

	 			trav_from = 0

	 			time1e = dateutil.parser.parse(str(event1['end']))
	 			time2s = dateutil.parser.parse(str(event2['start']))

	 			time_between_min = (time2s-time1e).total_seconds()/60
	 			if time_between_min>=appt_time:
	 				if event1['type']=='travel_block':
	 					trav_to = event1['length_min']
	 				if event2['type']=='travel_block':
	 					trav_from = event2['length_min']
	 				e = self.create_free_time_slot(time1e,time2s,trav_to,trav_from)
	 				free_time.append(e)

	 			trav_to = 0
	 			trav_from = 0

	 			if i==(len(temp_day_events)-2):
	 				time3 = dateutil.parser.parse(str(event2['end']))
	 				time_between_min = (stop_work_day-time3).total_seconds()/60
	 				if time_between_min>=appt_time:
	 					if event2['type']=='travel_block':
	 						trav_to = event2['length_min']
	 					e = self.create_free_time_slot(time3,stop_work_day,trav_to,trav_from)
	 					free_time.append(e)

	 			trav_to = 0

			#Free_time is now all the available slots in the day. 
			all_free_time+=free_time

		# print 'Ready To Make Appointment Slots'

		all_appt_slots = []

		for free_time in all_free_time:
			appt_slots = self.create_appt_slots(free_time,appt_time)

			appt_slots = self.final_appointment_processing(appt_slots,photographer,free_time)

			all_appt_slots+=appt_slots



  		return all_appt_slots
  		#return events+all_free_time+all_appt_slots




	def final_appointment_processing(self,events,photographer,free_time):
		

		for event in events:
			event['photog'] = photographer
			event['costFactor']+=[free_time['trav_to'],free_time['trav_from']]
			event['cost_est'] = self.calc_cost(event)

			# Add ANything or remove anything else hereself.
		return events




  	def create_appt_slots(self,free_time,appt_time,iter_n=0):
  		'''
  		This is a recursive appointment slot maker. 
  		'''
  		time1s = dateutil.parser.parse(str(free_time['start']))
	 	time1e = dateutil.parser.parse(str(free_time['end']))

	 	time1s = self.round_time(time1s, 5,  1)
	 	time1e = self.round_time(time1e, 5, -1)

		len_free_time = (time1e-time1s).total_seconds()/60

		max_overrun = 1.5 # 125%

		if len_free_time<appt_time:
			bias = (appt_time - len_free_time)/2
			ts = time1s - datetime.timedelta(0,bias*60)
			te = time1e + datetime.timedelta(0,bias*60)
			e = self.create_appt_event(ts,te,iter_n)
			return [e]
			#This is if the free time slow is shorter than the appt time. Center the appointment slot in the free time block. 

		elif len_free_time>=appt_time and len_free_time<(max_overrun*appt_time):
			#This is if we should have only one appointment in the free time. 
			e = self.create_appt_event(time1s, time1s+datetime.timedelta(0,appt_time*60), iter_n)
			return [e]

		elif len_free_time>=(max_overrun*appt_time) and len_free_time<(max_overrun*2*appt_time):
			#This is if we should have two appointments in the free time. They might overlap. 
			e1 = self.create_appt_event(time1s, time1s+datetime.timedelta(0,appt_time*60), iter_n)
			e2 = self.create_appt_event((time1e-datetime.timedelta(0,appt_time*60)), time1e, iter_n)
			return [e1,e2]

		elif len_free_time>=(max_overrun*2*appt_time):
			#The free time is bigger than 2 appts. Create two, then call this function again to recursively make appts. 
			e1 = self.create_appt_event(time1s, time1s+datetime.timedelta(0,appt_time*60), iter_n)
			e2 = self.create_appt_event((time1e-datetime.timedelta(0,appt_time*60)), time1e, iter_n)
			event_list = [e1,e2]
			n_free_time = self.create_free_time_slot(time1s+datetime.timedelta(0,appt_time*60),time1e-datetime.timedelta(0,appt_time*60))
			rec_list = self.create_appt_slots(n_free_time,appt_time,iter_n+1)
			return event_list+rec_list


	def get_calendar_events_with_travel(self, photographer,address,start_date,end_date, appt_time):
		print 'Start Date: %s' %str(start_date)
		print 'End Date: %s' %str(end_date)

		events = []
		try:
			cal_events = self.get_calendar_events(start_date,end_date,photographer)
			events = self.convert_goog_to_js(cal_events)
		except Exception as e:
			print 'Error with pulling calendar: %s' %e
			return self.ERROR

#		#Now lets add travel times from appointments to the current address. 
##		for event_i in all_events:#
#
		event_w_loc = []
		event_wo_loc = []
		travel_blocks = []
		event_w_travel = []
		
		for event_i in events:
			if event_i.has_key('location'):
				if event_i['location']!=None:
					event_w_loc.append(event_i)
				else:
					event_wo_loc.append(event_i)
				#event_i['location']='Hidden'

		# print '~~ Starting Travel Time Analysis ~~'

		if len(event_w_loc)==1:
			event = event_w_loc[0]
			time01 = dateutil.parser.parse(str(event['start']))
			time02 = dateutil.parser.parse(str(event['end']))

			start_loc = event['location']
			mid_loc = address 

			tr_time = self.get_travel_time(start_loc,mid_loc)
			e1 = self.create_travel_block(time01-datetime.timedelta(0,tr_time*60), time01,'Travel Time One Event' )
			e2 = self.create_travel_block(time02,time02+datetime.timedelta(0,tr_time*60),'Travel Time One Event' )
			event_w_travel.append(e1)
			event_w_travel.append(event)
			event_w_travel.append(e2)


		#This for loop should create a list of all events, in order, 
		# including travel times. It always adds travel events after event[i]. 
		for i in range(0,len(event_w_loc)-1):
			#print "Current i: %i out of: %i" %(i,len(event_w_loc)-1)
			event1 = event_w_loc[i]
			event2 = event_w_loc[i+1]

			event_w_travel.append(event1)

			start_loc = event1['location']
			end_loc = event2['location']
			mid_loc = address 

			time1 = dateutil.parser.parse(str(event1['end']))
			time2 = dateutil.parser.parse(str(event2['start']))

			# See If the next event starts before the current event ends, you are double booked.
			if time2<time1:
				print 'YOU ARE DOUBLE BOOKED!!!'
				event_w_travel.append(event1)
				continue

			#If this is the first event, make a travel block first. 
			if i==0:
				time9 = dateutil.parser.parse(str(event1['start']))
				tr_time = self.get_travel_time(mid_loc,start_loc)
				title = 'FIRST Travel Time'
				e = self.create_travel_block( (time9-datetime.timedelta(0,tr_time*60)) ,time9,title)
				event_w_travel.append(e)


			#Special check to see if the previous event is longer than the current, 
				#indicating some sort of nested or double booked events. 
				#Use the later time. 
			elif i>0:
				time30 = dateutil.parser.parse(str(event1['end']))
				time40 = dateutil.parser.parse(str(event_w_loc[i-1]['end']))
				if time40>time30:
					print 'Previous Event is Longer Than Current.'
					time1 = time40

			

			time_between_min = (time2-time1).total_seconds()/60
	#		print 'Block is: %i min wide' %time_between_min

			#if the window is smaller than the appointment time, make the block. 
			if (1.25*appt_time)>time_between_min and i<(len(event_w_loc)-2):
				title = 'Time Window Too Small'
				e = self.create_travel_block(time1,time2,title)
				#print 'Created A Fast Travel Block'
				event_w_travel.append(e)
				continue
			 
			travel_time1 = self.get_travel_time(start_loc,mid_loc)
			travel_time2 = self.get_travel_time(mid_loc,end_loc)

			#Lets Saturate travel times. THIS NEEDS TO THROW A WARNING.
			if travel_time1>180:
				travel_time1 = 180
				print 'WARNING: TRAVEL TIME FROM START TO APPT EXCESSIVE. Check Calendar Locations.'
			if travel_time2>180:
				print 'WARNING: TRAVEL TIME FROM APPT TO END EXCESSIVE. Check Calendar Locations.'
				travel_time2 = 180

			total_requirement = travel_time1+travel_time2+appt_time

			if total_requirement>time_between_min:
				title = 'Time Window Too Small'
				e = self.create_travel_block(time1,time2,title)
				event_w_travel.append(e)

			else:
				title = 'Travel Time'
				e1 = self.create_travel_block(time1 , (time1+datetime.timedelta(0,travel_time1*60)),title+' After')
				e2 = self.create_travel_block((time2-datetime.timedelta(0,travel_time2*60)),time2,title+' Before')

				event_w_travel.append(e1)
				event_w_travel.append(e2)

			#last block and last travel block.
			
			if i==(len(event_w_loc)-2):
				# print 'Im on the last event: %s' %event2['title']
				event_w_travel.append(event2)

				time10 = dateutil.parser.parse(str(event2['end']))
				travel_time3 = self.get_travel_time(end_loc,mid_loc)
				time20 = time10 + datetime.timedelta(0,travel_time3*60)
				title = 'Travel Time'
				#create travel event 
				e3 = self.create_travel_block(time10,time20,title)
				event_w_travel.append(e3)
				

		# print '~~ End Travel Time Analysis ~~'
# 
		return event_w_travel+event_wo_loc #events+travel_blocks


	def create_travel_block(self,start,end,title):

		output = {}
		output['title'] = title
		output['type'] = 'travel_block'
		output['start'] = start.isoformat()
		output['end']	= end.isoformat()
		output['length_min'] = (end-start).total_seconds()/60
		output['allDay']= False
		output['className']= 'event-red'

		return output

	def create_appt_event(self,start,end,cfac,title=''):

		output = {}
		output['type'] = 'appt_block'
		output['title'] = 'Available Appointment%s' %title
		output['start'] = start.isoformat()
		output['startStr'] = start.isoformat()
		output['end']	= end.isoformat()
		output['stop']	= end.isoformat()
		output['stopStr']	= end.isoformat()
		output['allDay']= False
		output['className']= "event-green"
		output['costFactor']=[cfac]
		output['cost_est'] = 99
		output['appt_time'] = (end-start).total_seconds()/60


		return output

	def create_free_time_slot(self,start,end,trav_to=0,trav_from=0):

		output = {}
		output['type'] = 'free_time_block'
		output['title'] = 'free time'
		output['start'] = start.isoformat()
		output['end']	= end.isoformat()
		output['allDay']= False
		output['className']= "event-orange"
		output['trav_to'] = trav_to
		output['trav_from'] = trav_from #to be set later! when a freetime block is created, see what event1 and event 2 are. 

		return output


	def convert_goog_to_js(self,events):
		'''
		Use this function to connect the google event keys to the JS keys. 
		i.e. title vs summary, or other information that needs to be added. 
		This is used to protect what gets sent over the javascript, keeping the agents/phone-n private
		'''
		output_list = []

		for event in events:
			try:
				output = {}
				output['type'] = 'gcal_event'
				if event['summary']=='Remark Visions Appointment':
					output['title']=event['summary']
				else:
					output['title']= event['summary']#'Busy'


				
				if event['start'].has_key('dateTime'):
					output['start']=event['start']['dateTime']
					output['end']=	event['end']['dateTime']
					output['allDay']=False
				elif event['start'].has_key('date'):
					#print 'Observed All Day Event: %s' %event['summary']
					start = dateutil.parser.parse(event['start']['date'])
					stop = start + datetime.timedelta(0,23*3600+59*60)
					output['start']=start.isoformat()
					output['end']=stop.isoformat()
					output['allDay']=False
				else:
					continue

			except Exception as e:
				print 'Error in Processing GCal Event: %s' %str(event)
				print 'Error: %s' %str(e)
				continue

			if event.has_key('location'):
				output['location']=event['location']
			else:
				output['location']=None
			output_list.append(output)

		return output_list


	def create_appointment(self, photographer, agent, address, start, end, phone_n,products, details, title):
		
		title = 'Remark Visions Appointment'
		#stop = start + datetime.timedelta(minutes=appt_time)
		timezone = None#'America/New_York'
		event = self.create_calendar_event(title,address,start,end,timezone,photographer,agent,phone_n,products, details)

		return event


	def round_time(self,time, round_to, sign):

		rounded = time + datetime.timedelta(minutes=round_to/2.)
		rounded -= datetime.timedelta(minutes=rounded.minute % round_to,
										seconds=rounded.second,
										microseconds=rounded.microsecond)
		#dir is positive:
		if sign>0:
			if rounded>=time:
				return rounded
			else: #rounded<time
				rounded+=datetime.timedelta(minutes=round_to)
				return rounded
		if sign<0:
			if rounded>time:
				rounded-=datetime.timedelta(minutes=round_to)
				return rounded
			else: #rounded<time
				return rounded





##### BLOCK CREATION ########

	def get_travel_time(self,start_adr, stop_adr):

		url = "http://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN".format(str(start_adr),str(stop_adr))
		result= simplejson.load(urllib.urlopen(url))
		driving_time_sec = result['rows'][0]['elements'][0]['duration']['value']
		#print("Travel Time: %i sec")%(driving_time)

		#RETURN TRAVEL TIME IN MINUTES
		driving_time_min = driving_time_sec/60.0

		if driving_time_min<5:
			driving_time_min=5
		return driving_time_min




	def get_calendar_events(self,start_dt,end_dt, p_name):
		"""Basic usage of the Google Calendar API.
		"""
		
		#now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
		start_time = start_dt.isoformat() + 'Z'
		end_time = end_dt.isoformat() + 'Z'

		photographer = self.photographer_ids.get(p_name)
	
		eventsResult = self.service.events().list(
			calendarId=photographer, timeMin=start_time, timeMax=end_time, 
			maxResults=100, singleEvents=True,
			orderBy='startTime').execute()

		events = eventsResult.get('items', [])

		if not events:
			print 'No upcoming events found.'
			events = []
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			stop = event['end'].get('dateTime')
			#print start, stop, event['summary']

		return events



	def create_calendar_event(self,title,address,start,stop,timezone,photographer='',agent='',phone_n='',products='None Listed',details=['']):

		desc_str = 'Agent: '+str(agent)+\
		'\nPhone Number: '+str(phone_n)+\
		'\nAddress: '+str(address) +\
		'\nPhotographer: '+str(photographer)+\
		'\nProducts: '+str(products)+\
		'\nDetails: '+str(details)


		event = {
		'summary': title,
		'location': address,
		'description': desc_str,
		'start': {
		'dateTime': start.isoformat(),
		'timeZone': timezone,
		},
		'end': {
		'dateTime': stop.isoformat(),
		'timeZone': timezone,
		},
		}

		calID = self.photographer_ids.get(photographer)

		event = self.service.events().insert(calendarId=calID, body=event).execute()
		print 'Event created: %s' % (event.get('htmlLink'))

		return event 
	   

##### GOOGLE SERVICES #########

	def setup_service(self):
		http = self.credentials.authorize(httplib2.Http())
		service = discovery.build('calendar', 'v3', http=http)
		return service


	def setup_credentials(self):
		"""Gets valid user credentials from storage.

		If nothing has been stored, or if the stored credentials are invalid,
		the OAuth2 flow is completed to obtain the new credentials.

		Returns:
		    Credentials, the obtained credential.
		"""
		home_dir = os.path.expanduser('~')
		credential_dir = os.path.join(home_dir, '.credentials')
		if not os.path.exists(credential_dir):
			os.makedirs(credential_dir)
		credential_path = os.path.join(credential_dir,
		                               'calendar-python.json')

		store = Storage(credential_path)
		credentials = store.get()
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(self._CLIENT_SECRET_FILE, self._SCOPES)
			flow.user_agent = self._APPLICATION_NAME
			
			if self._flags:
				credentials = tools.run_flow(flow, store, self._flags)
			else: # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
		return credentials




