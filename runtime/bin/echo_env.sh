#!/usr/bin/env bash
set -e

export ECHO_WS="${ECHO_WS:-$HOME/Echo}"
export ECHO_RUNTIME_DIR="${ECHO_RUNTIME_DIR:-$ECHO_WS/runtime}"

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
