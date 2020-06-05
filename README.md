# of-switch-tester

Provides base framework for simple testing of throughput of and OpenFlow
switch based on Ryu.

## Requirements

- An OpenFlow switch
- docker
- docker-compose > 2.1
- python3
- Python Requests package

## Installation

1.  First build the docker Ryu container with
`docker build -t ryu ryu`
2.  Run `docker-compose up -d` which will download the OpenTSDB docker
image the first time.
3.  Look at `switch_test_runner.py` for some example test cases (feel free
to contribute more)

## Operations

`docker-compose up` will start 2 docker containers

1.  OpenTSDB - a self contained OpenTSDB server
2.  Ryu - the Ryu OpenFlow controller running 3 applications
    
    **ryu.app.ofctl_rest** - provides REST interface for common operations such
    as stats request, flow crud, etc (documentation can be found at
    https://ryu.readthedocs.io/en/latest/app/ofctl_rest.html)
    **RyuToOpentsdb** - queries connected switches every 10 seconds and record
    of_port_stats_reply and of_flow_stats_reply into OpenTSDB
    **TpnRyuUtils** - provides a REST endpoint for sending packet outs
    
Once the containers are running point your OpenFlow switch at the Ryu 
container on port 6653 (can be changed in docker-compose).  Then run your
switch_test_runner.py and watch the pretty graphs in OpenTSDB.

### TpnRyuUtils

Provides a single rest endpoint

`POST http://hostname:8080/tpn/packet_out/{switchid}/{port}/{pkt_size}/{count}`

Where

switchid = DPID of the target switch
port = port number to send the Packet Out
pkt_size = total size of the packet including the header
count = number of packet out's to send (need at least 1)

Packet Out will be a UDP packet with a payload of all 0's and these for
the header:

DL_DST = '11:22:33:44:55:66'
DL_SRC = '66:55:44:33:22:11'
DL_TYPE = ether.ETH_TYPE_IP
IP_SRC = '1.1.1.1'
IP_DST = '2.2.2.2'
IP_PROTO = inet.IPPROTO_UDP


Good Luck! 