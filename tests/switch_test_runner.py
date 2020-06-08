#!/usr/bin/env python

import requests
import argparse
import logging
import time
import tests.noviflow_flows as novi

OFPP_IN_PORT = 4294967288

COOKIE_LOOP = 100
COOKIE_GOTO_TABLE = 101
COOKIE_SNAKE = 102
COOKIE_VLAN = 103

STATS_INTERVAL = 10  # This is set in OpenTsdbCollector


def get_response(action, url, json=None, headers=None):

    if action == "GET":
        r = session.get(url)
    elif action == "POST":
        r = session.post(url, json=json, headers=headers)
    elif action == "DELETE":
        r = session.delete(url)
    else:
        raise SyntaxError("Unknown Request Action: {}".format(action))

    r.raise_for_status()
    return r


def delete_all_flows():
    url = 'http://{}:{}/stats/flowentry/clear/{}'.format(args.hostname, args.port, args.dpid)
    get_response("DELETE", url)
    logger.warning("Deleted all flows for %s", args.dpid)


def add_flow(flowmod):
    url = 'http://{}:{}/stats/flowentry/add'.format(args.hostname, args.port)
    headers = {'Content-Type': 'application/json'}
    logger.debug("sending flowmod")
    logger.debug(flowmod)
    response = get_response("POST", url, json=flowmod, headers=headers)
    return response


def shut_port(port_no, action):
    url = 'http://{}:{}/stats/portdesc/modify'.format(args.hostname, args.port)
    headers = {'Content-Type': 'application/json'}

    if action == "up":
        state = 0
    else:
        state = 1

    data = {
        "dpid": args.dpid,
        "port_no": port_no,
        "config": state,
        "mask": 1
    }
    response = get_response("POST", url, json=data, headers=headers)
    return response


def flow_loop_all_ports(table_id, priority):
    flowmod = {
        'dpid': args.dpid,
        'cookie': COOKIE_LOOP,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': "OUTPUT",
                'port': OFPP_IN_PORT
            }
        ]
    }
    add_flow(flowmod)
    logger.info("Added loop flow to table %i", table_id)


def flow_goto_table(table_id, dst_table, priority):
    flowmod = {
        'dpid': args.dpid,
        'cookie': COOKIE_GOTO_TABLE,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': "GOTO_TABLE",
                'table_id': dst_table
            }
        ]
    }
    add_flow(flowmod)
    logger.info("Added goto_table for all packets from table %i to %i", table_id, dst_table)


def flow_snake(start_port, end_port, table_id, priority=1000):
    if end_port < start_port:
        raise ValueError

    flowmod = {
        'dpid': args.dpid,
        'cookie': COOKIE_SNAKE + table_id,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': 'OUTPUT',
                'port': -1
            }
        ]
    }

    logger.info("creating snake flow forward direction from port %i to %i in table %i",
                start_port, end_port, table_id)
    x = start_port
    if table_id == 5:
        logger.debug("doing table 5")
    while x < end_port - 2:
        flowmod['match'] = {'in_port': x + 1}
        flowmod['actions'][0]['port'] = x + 2
        add_flow(flowmod)
        x += 2
    flowmod['match'] = {'in_port': end_port}
    flowmod['actions'][0]['port'] = start_port
    add_flow(flowmod)

    logger.info("creating snake flow reverse direction from port %i to %i in table %i",
                start_port, end_port, table_id)
    x = end_port
    while x > start_port + 2:
        flowmod['match'] = {'in_port': x - 1}
        flowmod['actions'][0]['port'] = x - 2
        add_flow(flowmod)
        x -= 2
    flowmod['match'] = {'in_port': start_port}
    flowmod['actions'][0]['port'] = end_port
    add_flow(flowmod)


def flow_vlan_push_pop(in_port, out_port, action, vid=42, table_id=0, priority=2000):
    actions = [{
                'type': 'OUTPUT',
                'port': out_port
                }]
    if action == 'push':
        actions.insert(0, {'type': 'PUSH_VLAN', 'ethertype': 33024})
        actions.insert(1, {'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': vid})
    else:
        actions.insert(0, {'type': 'POP_VLAN'})

    flowmod = {
        'dpid': args.dpid,
        'cookie': COOKIE_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }
    add_flow(flowmod)


def flow_vxlan_push_pop(in_port, out_port, action, table_id=0, priority=2000,
                        src_ip='192.168.0.1', dst_ip='192.168.0.2',
                        src_mac='112233445566', dst_mac='aabbccddeeff',
                        udp_port=5000, vni=4242):
    actions = [{
        'type': 'OUTPUT',
        'port': out_port
    }]
    if action == 'push':
        vxlan_action = novi.make_experimenter_action(
            novi.action_payload_vxlan_push(src_ip, dst_ip, src_mac, dst_mac, udp_port, vni))
    else:
        vxlan_action = novi.make_experimenter_action(novi.action_payload_vxlan_pop())
    actions.insert(0, vxlan_action)

    flowmod = {
        'dpid': args.dpid,
        'cookie': COOKIE_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }
    add_flow(flowmod)

def send_packet_out(port, pkt_size, count):
    url = 'http://{}:{}/tpn/packet_out/{}/{}/{}/{}'.format(
        args.hostname, args.port, args.dpid, port, pkt_size, count)
    get_response("POST", url)
    logger.debug("Sending %i packet out to port %i of size %i", count, port, pkt_size)


def switch_at_peak_load(host=opentsdb_host, port=4242):
    logger.debug("Checking if switch at peak load")
    url = "http://{}:{}/api/query".format(host, port)
    payload = {"start": "30s-ago",
               "queries": [{"aggregator": "sum",
                            "metric": "port.bits",
                            "rate": "true",
                            "downsample": "10s-avg",
                            "tags": {}
                            }
                           ]
               }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, json=payload)
    response.raise_for_status()

    dps = sorted(response.json()[0]['dps'].items())
    if len(dps) < 2:
        logger.error("Somehow we only received 1 datapoint from OpenTSDB, %s", dps)
        return False  # What the hell try again
    curr = dps[-1][1]
    prev = dps[-2][1]

    if curr < 1000:  # arbitrary number to make sure we have some packets moving
        return False

    growth_rate = abs(curr - prev) / curr * 100
    logger.debug("growth is %f", growth_rate)

    if growth_rate == 0:
        return False  # Hack to deal with fact pushing packets every second but TSDB updated every minute
                      # has the risk of never finishing...

    return growth_rate < 0.05


def bring_switch_full_load(port, size, sleep=30):
    logger.info("Bringing switch to full load")
    done = False
    pkts_sent = 0
    while not done:
        send_packet_out(port, size, 1)
        pkts_sent += 1
        logger.debug("Injected %i packets per port in total", pkts_sent)
        time.sleep(1)
        done = switch_at_peak_load(args.hostname)
    logger.info("Injected %i packets with size of %i for port %i, tired so gonna sleep for %i seconds",
                pkts_sent, size, port, sleep)
    time.sleep(sleep)


def goto_table_test(size):
    logger.info("Performing GoTo Table test")

    flow_loop_all_ports(0, 100)
    flow_loop_all_ports(5, 100)
    flow_goto_table(1, 2, 100)
    flow_goto_table(2, 3, 100)
    flow_goto_table(3, 4, 100)
    flow_goto_table(4, 5, 100)

    bring_switch_full_load(-1, size)

    table = 5
    while table > 0:
        time.sleep(12 * STATS_INTERVAL)
        flow_goto_table(0, table, 200)
        table -= 1
    delete_all_flows()


def pps_test(port=-1, size=9000, type="loop"):
    logger.info("Performing PPS test")

    if type == 'loop':
        flow_loop_all_ports(0, 100)
    elif type == 'snake':
        flow_snake(1, 28, 0)
    else:
        raise Exception("Unknown pps_test type")

    bring_switch_full_load(port, size)


def vlan_test(size=9000):
    flow_snake(1, 28, 0)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding push/pop rules")
    flow_vlan_push_pop(28, OFPP_IN_PORT, 'pop')
    flow_vlan_push_pop(1, OFPP_IN_PORT, 'push', vid=42)


def vxlan_test(size=9000):
    flow_snake(1, 28, 0)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding push/pop vxlan rules")
    flow_vxlan_push_pop(28, OFPP_IN_PORT, 'pop')
    flow_vxlan_push_pop(1, OFPP_IN_PORT, 'push', vni=4242)


def main():
    try:
        for test in args.tests:
            logger.info("Running %s test case", test)

            for size in args.packet_size:
                logger.info("Packet size of %i", size)
                delete_all_flows()
                time.sleep(10)  # need to wait until traffic has stopped
                if test == 'goto_table':
                    goto_table_test(size)
                elif test == 'pps':
                    pps_test(size=size)
                elif test == 'pps-snake':
                    pps_test(size=size, type="snake")
                elif test == 'vlan':
                    vlan_test(size)
                elif test == 'vxlan':
                    vxlan_test(size)
                time.sleep(120)  # collect data for 2 minutes
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
    delete_all_flows()


def parsecmdline():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('hostname', action='store', help='Name/IP of RYU Controller')
    parser.add_argument('dpid', action='store', help='DPID of Switch to Test')
    parser.add_argument('--port', action='store', default=8080, help='RYU Controller REST port')
    parser.add_argument('-t', '--tests', nargs='*', choices=['goto_table', 'pps', 'pps-snake', 'vlan', 'vxlan'],
                        default='pps', help='Tests to Run')
    parser.add_argument('-p', '--packet_size', nargs='*', default=9000, type=int, help='List of packet sizes to test')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    args = parsecmdline()
    session = requests.Session()
    main()