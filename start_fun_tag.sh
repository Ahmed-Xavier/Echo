#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/ahmed/ros2_ws/install/setup.bash
export PYTHONPATH=$PYTHONPATH:/opt/ros/jazzy/lib/python3.12/site-packages
export PYTHONUNBUFFERED=1

echo "Starting WebRTC Server..."
python3 /home/ahmed/webrtc_server.py &
sleep 5

echo "Starting AprilTag Detector..."
python3 /home/ahmed/apriltag_detector.py &
sleep 5

echo "Starting Fun Tag Listener..."
python3 /home/ahmed/fun_tag_listener.py &

wait
