#!/bin/sh
LAB=${D35_LAB_BASE:-/usr/retro/platform-lab}
MVP=${D35_MVP_BASE:-/usr/retro/snes-mvp}
if [ -f "$LAB/armed" ]; then
  exec /bin/sh "$LAB/launch.sh"
fi
exec /bin/sh "$MVP/launch-game-1.8.sh"
