import copy
import requests
import json
import csv
import sys
import time
import datetime


input_payload = {
    'vehicles':[],
    'jobs':[],
}

vehicle_template = {
    'id': -1,
    'start': [],
    'end': [],
    'time_window': [0,12*3600],
    'capacity': [20],
}

job_template = {
    'id': -1,
    'location': [],
    'service': 15*60,
    'delivery': [1],
}

_index: int = 1000

def get_uid():
    global _index
    r = _index
    _index += 1
    return r


_jobs = {}

def gen_jobs():
    global _jobs
    with open('input.csv','r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader][1:]
        jobs = []
        for line in lines:
            if len(line) != 2:
                print(f'{line} is invalid')
                continue
            loc = line[1].replace('"','')
            global job_template
            job = copy.deepcopy(job_template)
            job['id'] = get_uid()
            job['location'] = [float(x) for x in loc.split(',') ]
            _jobs[job['id']] = {
                'name': line[0],
                'job': job,
            }
            jobs.append(job)
        return jobs

def gen_vehicle(lng, lat):
    global vehicle_template
    vehicle = copy.deepcopy(vehicle_template)
    vehicle['id'] = get_uid()
    vehicle['start'] = [lng,lat]
    vehicle['end'] = [lng,lat]
    return vehicle

def format_time(seconds):
    time = datetime.datetime(2000, 1, 1) + datetime.timedelta(seconds = seconds)
    return time.strftime("%I:%M %p")

def run():
    global input_payload
    headers = {
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Im5iLmFpIn0.eyJleHAiOjE5MDQ1MzUxMDguOTI3MDY5NywiYXVkIjpbIm5iIiwiZXZlcnl0aGluZyJdLCJjaWQiOiJjb21wYXNzIn0.N0YLGhXGVcyL1TKCL9r0-s7aCClSjVGWC286k3xiF76bW2CjULPH74ToojDs7OsOu_uRiq15cgfFBe7M-B6eda4tlcdZxVz1hR7czmTIxj0-hA03WvHlw3n-IS4af5PMNnqF7qXBIz4yVHRbTTLcuENwuQUbJmHkEdVXpQ8RzXMCorCCf3-gwWf46zpvnpiN6byYWF6yWRWXzU-7kDwz86ofrb0-lmj0ODMsPW7dB5_A6I5L2L5a-HPEfsxWi1678b7Grceqb2ZBbBZA7KHpAV5dVaKY7XBRynprAXSQBJ_23s2IDYo4osSRCs_NioV8gRjecGAZQHSJNwtnr_PZrw',
    }
    ip = copy.deepcopy(input_payload)
    ip['jobs'] = gen_jobs()
    vec_count = 0
    while vec_count < 10:
        vec_count += 1
        ip['vehicles'] = [gen_vehicle(77.1875135,28.4501651) for i in range(0,vec_count)]
        json.dump(ip, fp = open('build/input.json','w'), indent=4)
        r = requests.post('https://peelworks.nextbillion.io/optimise',json=ip, headers=headers)
        if r.status_code != 200:
            raise Exception(r.json())
        resp = r.json()
        if resp['code'] != 0:
            raise Exception(resp)
        unassigned = resp['summary']['unassigned']
        if unassigned == 0:
            break
        print(f'{vec_count} vehicles with {unassigned} unassigned jobs, will retry with more vehicles')
    print(f'all job assigned with {vec_count} vehicle(s)')
    json.dump(resp, fp = open('build/output.json','w'), indent=4)
    for i, route in enumerate(resp['routes']):
        with open(f'build/vehicle_{i}.csv', 'w') as f:
            lines = []
            lines.append(f'"Order ID", "Location", "Time"')
            for step in route['steps']:
                st = step['type']
                loc = ','.join([str(loc) for loc in step['location']][::-1])
                arrv = format_time(8*3600 + step['arrival'])
                if st == 'start' or st == 'end':
                    name = st
                else:
                    name = _jobs[step['job']]['name']
                    arrv = ''
                lines.append(f'"{name}","{loc}","{arrv}"')
            f.write('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise Exception('not enough arguments!')
    vehicle_template['capacity']  = [int(sys.argv[1])]   
    vehicle_template['time_window']  = [0,float(sys.argv[2])*3600]   
    run()

