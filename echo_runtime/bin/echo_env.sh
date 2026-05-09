#!/usr/bin/env bash
set -e

export ECHO_WS="/home/ahmed/.openclaw/workspace/github_echo/echo_workspace"

# ROS setup files may reference unset variables, so temporarily disable nounset.
case "$-" in
  *u*) _ECHO_RESTORE_NOUNSET=1 ;;
  *) _ECHO_RESTORE_NOUNSET=0 ;;
esac

set +u

source /opt/ros/jazzy/setup.bash

if [ -f "$ECHO_WS/install/setup.bash" ]; then
  source "$ECHO_WS/install/setup.bash"
else
  echo "ERROR: Echo workspace install not found: $ECHO_WS/install/setup.bash"
  if [ "$_ECHO_RESTORE_NOUNSET" = "1" ]; then set -u; fi
  return 1 2>/dev/null || exit 1
fi

if [ "$_ECHO_RESTORE_NOUNSET" = "1" ]; then
  set -u
fi

unset _ECHO_RESTORE_NOUNSET
