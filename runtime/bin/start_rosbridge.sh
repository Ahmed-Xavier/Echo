#!/usr/bin/env bash
set -euo pipefail

source "${ECHO_RUNTIME_DIR:-$HOME/Echo/runtime}/bin/echo_env.sh"

ROSBRIDGE_PORT="${ROSBRIDGE_PORT:-9090}"

echo "[echo-rosbridge] ECHO_WS=$ECHO_WS"
echo "[echo-rosbridge] starting rosbridge on port $ROSBRIDGE_PORT"

exec ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:="$ROSBRIDGE_PORT"
