#!/bin/bash
source /opt/ros/jazzy/setup.bash
ECHO_WS="${ECHO_WS:-$HOME/echo_workspace}"
ECHO_REPO_ROOT="${ECHO_REPO_ROOT:-$(cd "$ECHO_WS/.." && pwd)}"
source "$ECHO_WS/install/setup.bash"
export PYTHONPATH=$PYTHONPATH:/opt/ros/jazzy/lib/python3.12/site-packages
export PYTHONUNBUFFERED=1

echo "Starting WebRTC Server..."
python3 "$ECHO_REPO_ROOT/scripts/webrtc_server.py" &
sleep 5

echo "Starting AprilTag Detector..."
python3 "$ECHO_WS/src/echo_perception/scripts/apriltag_detector.py" &
sleep 5

echo "Starting Fun Tag Listener..."
python3 "$ECHO_REPO_ROOT/fun_tag_listener.py" &

wait
