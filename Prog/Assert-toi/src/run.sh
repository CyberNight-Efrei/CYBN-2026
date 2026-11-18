#!/bin/sh
ulimit -v 262144
ulimit -t 30
exec timeout 600 lua5.4 /app/server.lua
