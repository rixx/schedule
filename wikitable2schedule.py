 # -*- coding: UTF-8 -*-

import requests
import json
from collections import OrderedDict
import dateutil.parser
from datetime import datetime, time
from datetime import timedelta
import locale
import pytz
import os
import sys
import hashlib
import re

from voc.schedule import Schedule, ScheduleEncoder, Event, set_validator_filter


from bs4 import BeautifulSoup


days = []
de_tz = pytz.timezone('Europe/Amsterdam')
#local = False
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

# some functions used in multiple files of this collection
import voc.tools

voc.tools.set_base_id(1000)

year = 2020
wiki_url = 'https://di.c3voc.de/sessions-liste?do=export_xhtml#liste_der_self-organized_sessions'
output_dir = "/srv/www/schedule/divoc"
secondary_output_dir = "./divoc"


template = { "schedule": {
        "version": "1.0",
        "conference": {
            "title": "divoc - ptt",
            "acronym": "divoc3",
            "daysCount": 3,
            "start": "2020-09-04",
            "end":   "2020-09-06",
            "timezone": "+02:00",
            "timeslot_duration": "00:15",
            "days" : [],
            "base_url": "https://di.c3voc.de/",
        },
    }
}



if len(sys.argv) == 2:
    output_dir = sys.argv[1]

if not os.path.exists(output_dir):
    if not os.path.exists(secondary_output_dir):
        os.mkdir(output_dir) 
    else:
        output_dir = secondary_output_dir
        local = True
os.chdir(output_dir)

room_map = OrderedDict([
    ('Hauptraum', 1),
    ('Draussen', 20),
])

def get_room_id(room_name):

    if room_name in room_map:
        return room_map[room_name]
    else:
        return 0

def get_track_id(track_name):
    return 10
            
            

def main():
    global wiki_url, template, days
    

    # TODO refactor schedule class, to allow more generic templates

    out = template
    
    conference_start_date = dateutil.parser.parse(out['schedule']['conference']['start']+ "T00:00:00" + out['schedule']['conference']['timezone'])
    
    for i in range(out['schedule']['conference']['daysCount']):
        date = conference_start_date + timedelta(days=i)
        start = date + timedelta(hours=11)     # conference day starts at 11:00
        end = start + timedelta(hours=17) # conference day lasts 17 hours
        
        days.append( OrderedDict([
            ('index', i),
            ('date' , date),
            ('start', start),
            ('end', end),
        ]))
        
        
        out['schedule']['conference']['days'].append(OrderedDict([
            ('index', i+1),
            ('date' , date.strftime('%Y-%m-%d')),
            ('day_start', start.isoformat()),
            ('day_end', end.isoformat()),
            ('rooms', OrderedDict())
        ]))
    
    print("Requesting wiki events")
    
    # soup = BeautifulSoup(requests.get(wiki_url).text, 'html5lib')
    soup = BeautifulSoup(open("divoc-sessions.xhtml"), 'lxml')

    #sections = soup.find_all('h3')
    elements = soup.select('h3, table.inline')

    print('Processing sections')
    section_title = None
    for element in elements:
        if element.name == 'h3':
            section_title = element
            continue

        # ignore some sections
        if element.name == 'table':
            if section_title.attrs['id'] == 'durchgehende_treffpunkte_und_assemblies':
                continue

        day = section_title.text.split(',')[1].strip() + "{}".format(year)
        day_dt = datetime.strptime(day + out['schedule']['conference']['timezone'], '%d.%m.%Y%z') 

        # ignore sections which are not in target time span
        if day_dt < conference_start_date:
            continue

        rows = element.find_all('tr')

        # skip header row
        rows_iter = iter(rows)
        next(rows_iter)

        for row in rows_iter:
            data = {}
            for td in row.find_all('td'):
                #if type(td) != NoneType:
                key = td.attrs['class'][0]
                data[key] = re.compile(r'\s*\n\s*').split(td.get_text().strip())

            [start, end] = [ datetime.strptime(day + x + out['schedule']['conference']['timezone'], '%d.%m.%Y%H:%M%z') for x in re.compile(r'\s*(?:-|–)\s*').split(data['col0'][0]) ]
            title = data['col1'][0]
            abstract = data['col1'][1:]
            persons = data['col2'][0]
            links = data['col2'][1:]

            guid = voc.tools.gen_uuid('{}-{}'.format(start, links[0]))   
            local_id = voc.tools.get_id(guid)
            duration = (end - start).total_seconds()/60
            
            room = 'Internet'
            
            event_n = OrderedDict([
                ('id', local_id),
                ('guid', guid),
                # ('logo', None),
                ('date', start.isoformat()),
                ('start', start.strftime('%H:%M')),
                ('duration', '%d:%02d' % divmod(duration, 60)),
                ('room', room),
                ('slug', '{slug}-{id}-{name}'.format(
                        slug=out['schedule']['conference']['acronym'].lower(),
                        id=local_id,
                        name=voc.tools.normalise_string(title.lower())
                    )),
                ('title', title),
                ('subtitle', ''),
                ('track', 'Workshop'),
                ('type', 'Workshop'),
                ('language', 'de' ),
                ('abstract', abstract or ''),
                ('description', '' ),
                ('persons', [ OrderedDict([
                    ('id', 0),
                    ('public_name', p.strip()),
                    #('#text', p),
                ]) for p in persons.split(',') ]),
                ('links', links)
            ])
            
            day_rooms = out['schedule']['conference']['days'][get_day(start)]['rooms']
            if room not in day_rooms:
                day_rooms[room] = []
            day_rooms[room].append(event_n)
        
            sys.stdout.write('.')
        
            
    print(json.dumps(out, indent=2))
    
    schedule = Schedule(json=out)
    schedule.export('wiki')
    
    print('')
    print('end')

def get_day(start_time):
    for day in days:
        if day['start'] <= start_time < day['end']:
            # print "Day {0}: day.start {1} <= start_time {2} < day.end {3}".format(day['index'], day['start'], start_time, day['end'])
            # print "Day {0}: day.start {1} <= start_time {2} < day.end {3}".format(day['index'], day['start'].strftime("%s"), start_time.strftime("%s"), day['end'].strftime("%s"))
            return day['index']
    
    print("  illegal start time: " + start_time.isoformat())   
    return None

def first(x):
    if len(x) == 0:
        return None
    else:
        return x[0]

if __name__ == '__main__':
    main()

if not local:  
    os.system("git add *.json *.xml")
    os.system("git commit -m 'updates from " + str(datetime.now()) +  "'")
    os.system("git push")
