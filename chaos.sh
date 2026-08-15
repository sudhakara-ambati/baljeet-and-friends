#!/bin/bash
cleanup() { docker rm -f broke-$1 2>/dev/null; }

case "$1" in
  loud)
    cleanup loud
    docker run -d --name broke-loud alpine sh -c \
      "echo 'FATAL: cannot open /config/db.sqlite3: permission denied' >&2; exit 1" ;;
  silent)
    cleanup silent
    docker run -d --name broke-silent alpine sh -c "exit 1" ;;
  oom)
    cleanup oom
    docker run -d --name broke-oom -m 16m alpine sh -c \
      "dd if=/dev/zero of=/dev/shm/f bs=1M count=100" ;;
  loop)
    cleanup loop
    docker run -d --restart=always --name broke-loop alpine sh -c \
      "sleep 15; exit 1" ;;
  mystery)
    cleanup mystery
    docker run -d --name broke-mystery nginx
    sleep 3
    docker kill --signal=SIGKILL broke-mystery ;;
  clean)
    docker rm -f $(docker ps -aq) 2>/dev/null ;;
  *) echo "usage: ./chaos.sh {loud|silent|oom|loop|mystery|clean}" ;;
esac