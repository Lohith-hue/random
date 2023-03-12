set -e
service_time=900
vehicle_hours=12
day=`date '+%Y%m%d' --date='1 day'`
fleet_order='unrestricted_first'
rm -rf build || true
mkdir build || true
python compute.py $service_time $vehicle_hours $day $fleet_order
zip output.zip -r build
