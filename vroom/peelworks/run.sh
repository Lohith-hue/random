set -e
vehicle_capacity=15
vehicle_hours=12
rm -rf build || true
mkdir build || true
rm output.zip || true
python compute.py $vehicle_capacity $vehicle_hours
zip output.zip -r build
