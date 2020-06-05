#!/bin/sh

echo "Starting ryu.  It should be available on port 8080 momentarily."

cd /files
ryu-manager --verbose RyuToOpentsdb.py TpnRyuUtils.py ryu.app.ofctl_rest &

while [ 1 ]
do
    sleep 1
done
