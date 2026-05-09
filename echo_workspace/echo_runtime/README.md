# Echo Runtime Dashboard

Runtime support files for Echo's local browser dashboard.

## Always-on Pi services

These run automatically after Pi reboot:

- `echo-rosbridge.service`
  - starts `rosbridge_server`
  - WebSocket: `ws://PI_IP:9090`

- `echo-launch-server.service`
  - starts the local launch control API
  - HTTP: `http://PI_IP:5050`

These services do **not** start the robot body stack. They do not start micro-ROS, LiDAR, SLAM, Nav2, camera, or motors.

## Dashboard-controlled actions

Currently enabled:

- `camera`
  - starts the USB camera publisher and AprilTag detector
  - final dashboard topic: `/apriltag/annotated_image/compressed`

- `foxglove`
  - starts `foxglove_bridge`
  - WebSocket: `ws://PI_IP:8765`

Currently disabled until the robot body is attached:

- `mapping`
- `navigation`
- `stop_stack`

## API

Health:

    curl http://PI_IP:5050/health

Status:

    curl http://PI_IP:5050/status

Start camera:

    curl -X POST http://PI_IP:5050/launch -H "Content-Type: application/json" -d '{"action":"camera"}'

Stop camera:

    curl -X POST http://PI_IP:5050/stop -H "Content-Type: application/json" -d '{"action":"camera"}'

Read logs:

    curl "http://PI_IP:5050/logs?action=camera&lines=50"

## Runtime ports

| Port | Service | Purpose |
|---:|---|---|
| `9090` | `rosbridge_server` | ROS WebSocket for the browser dashboard |
| `5050` | `echo-launch-server` | HTTP launch/status/logs API |
| `8765` | `foxglove_bridge` | Foxglove WebSocket, started on demand |

## Camera topic

The dashboard uses the annotated AprilTag stream:

    /apriltag/annotated_image/compressed

The raw camera topic is only an internal input for the AprilTag detector.

## Install services on the Pi

From the repository root:

    mkdir -p ~/.config/systemd/user
    cp echo_workspace/echo_runtime/systemd/*.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now echo-rosbridge.service
    systemctl --user enable --now echo-launch-server.service
    sudo loginctl enable-linger "$USER"

## Useful checks

    systemctl --user status echo-rosbridge.service --no-pager
    systemctl --user status echo-launch-server.service --no-pager
    ss -ltnp | grep -E '9090|5050|8765'
    curl http://127.0.0.1:5050/status | python3 -m json.tool
