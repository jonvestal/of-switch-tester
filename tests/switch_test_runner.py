#!/usr/bin/env python

import argparse
import logging
import time

import requests

import flows as flows
from constants import *

TEST_CASES = ['goto_table', 'pps', 'pps-snake', 'vlan', 'vxlan', 'swap', 'copy']
HTTP_HEADERS = {'Content-Type': 'application/json'}
SNAKE_FIRST_PORT = 5
SNAKE_LAST_PORT = 28


def delete_all_flows():
    url = 'http://{}:{}/stats/flowentry/clear/{}'.format(args.hostname, args.port, args.dpid)
    resp = session.delete(url)
    resp.raise_for_status()
    logger.warning("Deleted all flows for %s", args.dpid)


def add_flow(flowmod):
    url = 'http://{}:{}/stats/flowentry/add'.format(args.hostname, args.port)
    logger.debug("sending flowmod %s", flowmod)
    response = session.post(url, json=flowmod, headers=HTTP_HEADERS)
    response.raise_for_status()
    return response


def shut_port(port_no, action):
    url = 'http://{}:{}/stats/portdesc/modify'.format(args.hostname, args.port)
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
    response = session.post(url, json=data, headers=HTTP_HEADERS)
    response.raise_for_status()
    return response


def send_packet_out(port, pkt_size, count):
    url = 'http://{}:{}/tpn/packet_out/{}/{}/{}/{}'.format(
        args.hostname, args.port, args.dpid, port, pkt_size, count)
    resp = session.post(url)
    resp.raise_for_status()
    logger.debug("Sending %i packet out to port %i of size %i", count, port, pkt_size)


def switch_at_peak_load(host, port=4242):
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
    response = requests.post(url, headers=HTTP_HEADERS, json=payload)
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
        done = switch_at_peak_load(args.otsdb_hostname)
    logger.info("Injected %i packets with size of %i for port %i, tired so gonna sleep for %i seconds",
                pkts_sent, size, port, sleep)
    time.sleep(sleep)


def goto_table_test(size):
    logger.info("Performing GoTo Table test")

    add_flow(flows.flow_loop_all_ports(args.dpid, 0, 100))
    add_flow(flows.flow_loop_all_ports(args.dpid, 5, 100))
    add_flow(flows.flow_goto_table(args.dpid, 1, 2, 100))
    add_flow(flows.flow_goto_table(args.dpid, 2, 3, 100))
    add_flow(flows.flow_goto_table(args.dpid, 3, 4, 100))
    add_flow(flows.flow_goto_table(args.dpid, 4, 5, 100))

    bring_switch_full_load(-1, size)

    table = 5
    while table > 0:
        logger.info("collecting data for tables = %i", 5 - table + 1)
        time.sleep(args.collection_interval)
        add_flow(flows.flow_goto_table(args.dpid, 0, table, 200))
        table -= 1


def pps_test(port=-1, size=9000, type="loop"):
    logger.info("Performing PPS test")

    if type == 'loop':
        add_flow(flows.flow_loop_all_ports(args.dpid, 0, 100))
    elif type == 'snake':
        flowmods = flows.flow_snake(args.dpid, SNAKE_FIRST_PORT, SNAKE_LAST_PORT, 0)
        for flow in flowmods:
            add_flow(flow)
    else:
        raise Exception("Unknown pps_test type")

    bring_switch_full_load(port, size)


def vlan_test(size=9000):
    flowmods = flows.flow_snake(args.dpid, SNAKE_FIRST_PORT, SNAKE_LAST_PORT, 0)
    for flow in flowmods:
        add_flow(flow)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding push/pop rules")
    add_flow(flows.flow_vlan_push_pop(args.dpid, SNAKE_LAST_PORT, OFPP_IN_PORT, 'pop'))
    if not args.header_only:
        logger.info("Setting header values")
        add_flow(flows.flow_vlan_push_pop(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT, 'push', vid=42))
    else:
        add_flow(flows.flow_vlan_push_pop(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT, 'push'))


def vxlan_test(size=9000):
    for flow in flows.flow_snake(args.dpid, SNAKE_FIRST_PORT, SNAKE_LAST_PORT, 0):
        add_flow(flow)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding push/pop vxlan rules")
    add_flow(flows.flow_vxlan_pop(args.dpid, SNAKE_LAST_PORT, OFPP_IN_PORT))
    if not args.header_only:
        logger.info("Setting header values")
        add_flow(flows.flow_vxlan_push(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT, vni=4242))
    else:
        add_flow(flows.flow_vxlan_push(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT, flags=0))


def swap_test(size=9000):
    for flow in flows.flow_snake(args.dpid, SNAKE_FIRST_PORT, SNAKE_LAST_PORT, 0):
        add_flow(flow)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding swap fields rules")
    add_flow(flows.flow_swap_fields(args.dpid, SNAKE_LAST_PORT, OFPP_IN_PORT))
    add_flow(flows.flow_swap_fields(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT))


def copy_test(size=9000):
    for flow in flows.flow_snake(args.dpid, SNAKE_FIRST_PORT, SNAKE_LAST_PORT, 0):
        add_flow(flow)
    bring_switch_full_load(-1, size)

    logger.info("Switch under full load adding copy fields rules")
    add_flow(flows.flow_copy_fields(args.dpid, SNAKE_LAST_PORT, OFPP_IN_PORT))
    add_flow(flows.flow_set_fields(args.dpid, SNAKE_FIRST_PORT, OFPP_IN_PORT, {'eth_dst': 'aa:bb:cc:dd:ee:ff'}))


def main():
    max_runs = 1
    run_num = 0
    try:
        while run_num < max_runs:
            for test in args.tests:
                logger.info("Running %s test case, run number %i", test, run_num + 1)

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
                    elif test == 'swap':
                        swap_test(size)
                    elif test == 'copy':
                        copy_test(size)
                    else:
                        raise Exception("Invalid test case specified")
                    logger.info("Collecting data for %s with size %i for %i seconds",
                                test, size, args.collection_interval)
                    time.sleep(args.collection_interval)
            run_num += 1
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
    parser.add_argument('-t', '--tests', nargs='*', choices=TEST_CASES,
                        default='pps', help='Tests to Run')
    parser.add_argument('-p', '--packet_size', nargs='*', default=9000, type=int, help='List of packet sizes to test')
    parser.add_argument('--otsdb_hostname', action='store',
                        help='OpenTSDB server, if not specified uses RYU Controller')
    parser.add_argument('--collection_interval', action='store', default=120, type=int,
                        help='Period of time to collect after starting a test')
    parser.add_argument('--header_only', action='store_true', default=False,
                        help='Where applicable will only add the header and not set actual values')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    args = parsecmdline()
    if 'otsdb_hostname' not in args:
        args.otsdb_hostname = args.hostname

    session = requests.Session()
    main()
