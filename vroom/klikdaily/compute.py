import copy
import requests
import json
import csv
import datetime
import sys
import urllib.parse


class VehicleInput:
    def __init__(self, line):
        self.no = int(line[0])
        self.fleet_type = line[1]
        self.plate_number = line[2]
        self.odd_even = line[3]
        self.fleet_length = int(line[4])
        self.fleet_width = int(line[5])
        self.fleet_height = int(line[6])
        self.fleet_weight = int(line[7])


class JobInput:
    def __init__(self, line):
        try:
            self.invoiceId = line[0]
            self.address = line[1]
            self.state = line[2]
            self.city = line[3]
            self.district = line[4]
            self.postCode = line[5]
            self.storeStart = line[6]
            self.storeEnd = line[7]
            self.senderOrigin = line[8]
            self.returnOrigin = line[9]
            self.lng = float(line[10])
            self.lat = float(line[11])
            self.quantity = float(line[12])
            self.sku = line[13]
            self.length = float(line[14])
            self.height = float(line[15])
            self.width = float(line[16])
            self.weight = float(line[17])
            self.total_weight = 0
            self.total_volume = 0
        except Exception as e:
            print(line)
            raise e

_holidays = []

input_payload = {
    'vehicles': [],
    'shipments': [],
}

vehicle_template = {
    'id': -1,
    'start': [],
    'end': [],
    'time_window': [6 * 3600, 18 * 3600],
    'capacity': [],
}

shipment_template = {
    'amount': [],
    'pickup': {
        'id': -1,
        'location': [106.6809807, -6.335105727],
        'time_windows': [[6 * 3600, 18 * 3600]],
    },
    'delivery': {
        'id': -1,
        'location': [],
        'time_windows': [],
        'service': 15 * 60,
    },
}

_index: int = 1000

warehouse_loc = (106.6809807, -6.335105727)

def get_restriction(day):
    if day.weekday() == 5:
        return -1
    for h in _holidays:
        if day.year == h.year and day.month == h.month and day.day == h.day:
            return -1
    return day.day % 2


def get_uid():
    global _index
    r = _index
    _index += 1
    return r


_jobs = {}
_vehicles = {}
volume_ratio: float = 0.8


def gen_shipments():
    global _jobs
    with open('input.csv', 'r') as f:
        job_inputs = [JobInput(line) for line in [
            line for line in csv.reader(f, delimiter='\t')][1:]]
        shipments = []
        merged = {}
        for ji in job_inputs:
            total_weight = ji.weight * ji.quantity
            total_volume = ji.length * ji.width * ji.height * ji.quantity
            last = merged.get(ji.invoiceId, None)
            if not last:
                ji.total_weight = total_weight
                ji.total_volume = total_volume
                merged[ji.invoiceId] = ji
            else:
                last.total_weight += total_weight
                last.total_volume += total_volume
        for k, ji in merged.items():
            global shipment_template
            shipment = copy.deepcopy(shipment_template)
            shipment['pickup']['id'] = get_uid()
            shipment['delivery']['id'] = get_uid()
            shipment['delivery']['location'] = [ji.lng, ji.lat]
            shipment['amount'] = [ji.total_weight, ji.total_volume]
            ts = from_formatted_time(ji.storeStart)
            te = from_formatted_time(ji.storeEnd)
            if te <= ts:
                # this means it is next day
                te += 24 * 3600
            shipment['delivery']['time_windows'] = [[ts, te]]
            _jobs[shipment['delivery']['id']] = ji
            _jobs[shipment['pickup']['id']] = ji
            shipments.append(shipment)
    return shipments


def gen_vehicles(lng, lat, restriction, fleet_order):
    global vehicle_template
    global volume_ratio
    global _vehicles
    result=[([],'unrestricted'),([],'restricted')]
    restricted = result[1][0]
    unrestricted = result[0][0]
    if fleet_order == 'restricted_first':
        result=[([],'restricted'),([],'unrestricted')]
        restricted = result[0][0]
        unrestricted = result[1][0]
    with open('vehicles.csv', 'r') as f:
        vehicle_inputs = [VehicleInput(line) for line in [
            line for line in csv.reader(f)][1:]]
        for vi in vehicle_inputs:
            vehicle = copy.deepcopy(vehicle_template)
            vehicle['id'] = get_uid()
            vehicle['start'] = [lng, lat]
            vehicle['end'] = [lng, lat]
            vehicle_volume = vi.fleet_length * vi.fleet_width * vi.fleet_height * volume_ratio
            vehicle['capacity'] = [vi.fleet_weight, vehicle_volume]
            _vehicles[vehicle['id']] = vi
            if (restriction == 1 and vi.odd_even == 'ODD') or (restriction == 0 and vi.odd_even == 'EVEN') :
                restricted.append(vehicle) 
                continue
            unrestricted.append(vehicle) 
    return result


def format_time(seconds):
    time = datetime.datetime(2000, 1, 1) + datetime.timedelta(seconds=seconds)
    return time.strftime("%I:%M %p")


def from_formatted_time(thing):
    h, m = thing.split(':')
    return int(h) * 3600 + int(m) * 60


def update_state(state, job_type):
    if state == None:
        return 'warehouse loading'
    elif state == 'warehouse loading':
        if job_type == 'delivery':
            return 'delivery'
        else:
            return 'warehouse loading'
    elif state == 'delivery':
        if job_type == 'delivery':
            return 'delivery'
        elif job_type == 'pickup':
            return 'warehouse reloading'
        elif job_type == 'end':
            return 'end'
    elif state == 'warehouse reloading':
        if job_type == 'pickup':
            return 'warehouse reloading'
        elif job_type == 'delivery':
            return 'delivery'
    elif state == 'end':
        return 'end'

def run(restriction, fleet_order):
    global input_payload
    global _vehicles
    headers = {
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Im5iLmFpIn0.eyJleHAiOjE5MDQ1MzUxMDguOTI3MDY5NywiYXVkIjpbIm5iIiwiZXZlcnl0aGluZyJdLCJjaWQiOiJjb21wYXNzIn0.N0YLGhXGVcyL1TKCL9r0-s7aCClSjVGWC286k3xiF76bW2CjULPH74ToojDs7OsOu_uRiq15cgfFBe7M-B6eda4tlcdZxVz1hR7czmTIxj0-hA03WvHlw3n-IS4af5PMNnqF7qXBIz4yVHRbTTLcuENwuQUbJmHkEdVXpQ8RzXMCorCCf3-gwWf46zpvnpiN6byYWF6yWRWXzU-7kDwz86ofrb0-lmj0ODMsPW7dB5_A6I5L2L5a-HPEfsxWi1678b7Grceqb2ZBbBZA7KHpAV5dVaKY7XBRynprAXSQBJ_23s2IDYo4osSRCs_NioV8gRjecGAZQHSJNwtnr_PZrw',
    }
    ip = copy.deepcopy(input_payload)
    shipments = gen_shipments()
    vehicles_list = gen_vehicles(106.6809807, -6.335105727, restriction, fleet_order)
    for vehicles,speciality in vehicles_list:
        if len(shipments) == 0 or len(vehicles) == 0:
            break
        ip['shipments'] = shipments
        ip['vehicles'] = vehicles
        if speciality == 'restricted':
            ip['speciality'] = 'oddeven'
        json.dump(ip, fp=open(f'build/input-{speciality}.json', 'w'), indent=4)
        print(f'planning for {len(ip["shipments"])} shipments with {speciality} vehicle group[{len(vehicles)}] vehicles')
        r = requests.post('https://api.nextbillion.io/optimise', json=ip, headers=headers)
        #r = requests.post('http://localhost:8888/optimise',json=ip, headers=headers)
        if r.status_code != 200:
            raise Exception(f'optimise returns: {r.status_code}')
        resp = r.json()
        if resp['code'] != 0:
            raise Exception(resp)
        next_batch = []
        for u in resp['unassigned']:
            for s in shipments:
                if s['pickup']['id'] == u['id']:
                    next_batch.append(s)
                    break
        unassigned = int(resp['summary']['unassigned'] / 2)
        print(f'planned with {unassigned} unassigned shipments')
        json.dump(resp, fp=open(f'build/output-{speciality}.json', 'w'), indent=4)
        if unassigned > 0:
            with open('build/unassigned.csv', 'w+') as f:
                lines = []
                for uas in resp['unassigned']:
                    job = _jobs[uas['id']]
                    if not job.invoiceId in lines:
                        lines.append(job.invoiceId)
                f.write('\n'.join(lines))
        shipments = next_batch
        for route in resp['routes']:
            vehicle = _vehicles[route['vehicle']]
            state = update_state(None, None)
            coords = [','.join([str(x[1]),str(x[0])]) for x in [step['location'] for step in route['steps']]]
            waypoints = '|'.join(coords[1:-1])
            route_url = f'https://api.nextbillion.io/directions/json?origin={coords[0]}&destination={coords[-1]}&waypoints={waypoints}'
            if speciality == 'restricted':
                route_url = f'{direction_url}&speciality=oddeven'
            polyline = requests.get(route_url, headers=headers).json()['routes'][0]['geometry']
            img = requests.post(f'https://api.nextbillion.io/trip/image?polyline={polyline}',json={'polyline':polyline}).content
            open(f'build/vehicle_{vehicle.no}.jpg','wb').write(img)
            with open(f'build/vehicle_{vehicle.no}.csv', 'w') as f:
                lines = []
                lines.append('"Order ID", "Type", "Location", "Arrival", "Departure", "Driving Distance"')
                last_loc = None
                for step in route['steps']:
                    st = step['type']
                    state = update_state(state, st)
                    loc = ','.join([str(x) for x in step['location']])
                    arrv = format_time(step['arrival'])
                    cur_loc = ','.join([str(x) for x in step['location'][::-1]])
                    distance = 0
                    if last_loc:
                        direction_url = f'https://api.nextbillion.io/directions/json?origin={last_loc}&destination={cur_loc}'
                        if speciality == 'restricted':
                            direction_url = f'{direction_url}&speciality=oddeven'

                        distance = int(requests.get(direction_url, headers=headers).json()['routes'][0]['distance'])
                    if st == 'start' or st == 'end':
                        name = st
                        lines.append(f'"{name}","{state}","{loc}","{arrv}","{arrv}", "{distance}"')
                    else:
                        dept = format_time(step['arrival'] + step['service'])
                        name = _jobs[step['job']].invoiceId
                        lines.append(f'"{name}","{state}","{loc}","{arrv}","{dept}", "{distance}"')
                    last_loc = cur_loc
                f.write('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise Exception('not enough arguments!')
    shipment_template['delivery']['service'] = int(sys.argv[1])
    vehicle_template['time_window'] = [6 * 3600, (6 + int(sys.argv[2])) * 3600]
    day = sys.argv[3]
    if len(day) != 8:
        raise Exception(f'invalid date format: {day}, requires: YYYYMMDD')
    try:
        day = datetime.datetime.strptime(day, '%Y%m%d')
    except Exception as e:
        raise Exception(f'invalid date format, error: {e}')
    with open('holidays.txt') as f:
        _holidays = [datetime.datetime.strptime(line.strip(),'%Y%m%d') for line in f.readlines()]
    fleet_order = sys.argv[4]
    run(get_restriction(day), fleet_order)
