#!/usr/bin/env bash
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000

gsettings set org.gnome.desktop.session idle-delay 0 || true
gsettings set org.gnome.desktop.screensaver lock-enabled false || true
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false || true

xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true
