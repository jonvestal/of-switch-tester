import logging
import time
from datetime import datetime

import requests

from oftester.openflow import basic_flows as flows

HTTP_HEADERS = {'Content-Type': 'application/json'}


class Switch:
    def __init__(self, dpid, snake_start_port, snake_end_port, ingress_port, egress_port, traffgen_ports=None):
        self.dpid = self._format_dpid(dpid)
        self.snake_start_port = snake_start_port
        self.snake_end_port = snake_end_port
        self.ingress_port = ingress_port
        self.egress_port = egress_port

        if not traffgen_ports:
            traffgen_ports = []

        self.traffgen_ports = traffgen_ports

    def _format_dpid(self, dpid):
        if not dpid:
            raise ValueError('DPID must not be empty.')

        if dpid.isdigit():
            return dpid
        else:
            try:
                return str(int(dpid.replace(':', ''), 16))
            except Exception as e:
                raise ValueError('Unknown DPID format of %s' % dpid)


class Environment:
    def __init__(self, otsdb_host, otsdb_port, ryu_host, ryu_port, reports, switches):
        self.otsdb_host = otsdb_host
        self.otsdb_port = otsdb_port
        self.ryu_host = ryu_host
        self.ryu_port = ryu_port
        self.reports = reports
        switch_map = {}
        for sw_dict in switches:
            sw = Switch(**sw_dict)
            switch_map[sw.dpid] = sw
        self.switches = switch_map

    def sw_by_dpid(self, dpid):
        return self.switches[dpid]

class ScenarioTimestamps:
    pass


class Scenario:

    def __init__(self, name, environment, packet_sizes=None, collection_interval=120):
        self.name = name
        if not packet_sizes:
            packet_sizes = [9000]
        self.packet_sizes = packet_sizes
        self.current_packet_idx = 0
        self.collection_interval = collection_interval
        self.environment = Environment(**environment)
        self.session = requests.Session()
        self.time_metrics = [ScenarioTimestamps()]

    def run(self):
        raise NotImplementedError()

    def execute(self, run_num):
        logging.info('Running %s test case, run number %i', self.name, run_num + 1)
        size = self.current_packet_size()
        logging.info('Packet size of %i', size)
        self.delete_all_flows()
        self.time_metrics[-1].start = datetime.utcnow()
        self.run()
        time.sleep(10)  # need to wait until traffic has stopped
        logging.info('Collecting data for %s with size %i for %i seconds',
                     self.name, size, self.collection_interval)
        time.sleep(self.collection_interval)
        self.time_metrics[-1].stop = datetime.utcnow()
        self.delete_all_flows()
        if self.current_packet_idx < len(self.packet_sizes) -1:
            self.next_packet_size()


    def next_packet_size(self):
        self.current_packet_idx += 1
        self.time_metrics.append(ScenarioTimestamps())
        return self.current_packet_size()

    def current_packet_size(self):
        return self.packet_sizes[self.current_packet_idx]

    def delete_all_flows(self, dpid=None):
        if dpid:
            self._delete_all_flows(dpid)
        else:
            for sw in self.environment.switches.keys():
                self._delete_all_flows(sw)


    def _delete_all_flows(self, dpid):
        url = 'http://{}:{}/stats/flowentry/clear/{}'.format(self.environment.ryu_host, self.environment.ryu_port, dpid)
        resp = self.session.delete(url)
        resp.raise_for_status()
        logging.warning('Deleted all flows for %s', dpid)

    def add_flow(self, flowmod):
        url = 'http://{}:{}/stats/flowentry/add'.format(self.environment.ryu_host, self.environment.ryu_port)
        logging.debug('sending flowmod %s', flowmod)
        response = self.session.post(url, json=flowmod, headers=HTTP_HEADERS)
        response.raise_for_status()
        return response

    def shut_port(self, dpid, port_no, action):
        url = 'http://{}:{}/stats/portdesc/modify'.format(self.environment.ryu_host, self.environment.ryu_port)
        if action == 'up':
            state = 0
        else:
            state = 1

        data = {
            'dpid': dpid,
            'port_no': port_no,
            'config': state,
            'mask': 1
        }
        response = self.session.post(url, json=data, headers=HTTP_HEADERS)
        response.raise_for_status()
        return response

    def send_packet_out(self, dpid, port, outer_vlan, inner_vlan, vni, pkt_size, count):
        url = 'http://{}:{}/tpn/packet_out/{}'.format(
            self.environment.ryu_host, self.environment.ryu_port, dpid)
        resp = self.session.post(url, json={
            'port': port,
            'outer_vlan': outer_vlan,
            'inner_vlan': inner_vlan,
            'vni': vni,
            'pkt_size': pkt_size,
            'count': count
        })
        resp.raise_for_status()
        logging.debug('Sending %i packet out to port %i of size %i', count, port, pkt_size)

    def switch_at_peak_load(self):
        logging.debug('Checking if switch at peak load')
        url = 'http://{}:{}/api/query'.format(self.environment.otsdb_host,
                                              self.environment.otsdb_port)
        payload = {'start': '30s-ago',
                   'queries': [{'aggregator': 'sum',
                                'metric': 'port.bits',
                                'rate': 'true',
                                'downsample': '10s-avg',
                                'tags': {}
                                }
                               ]
                   }
        response = requests.post(url, headers=HTTP_HEADERS, json=payload)
        response.raise_for_status()

        dps = sorted(response.json()[0]['dps'].items())
        if len(dps) < 2:
            logging.error('Somehow we only received 1 datapoint from OpenTSDB, %s', dps)
            return False  # What the hell try again
        curr = dps[-1][1]
        prev = dps[-2][1]

        if curr < 1000:  # arbitrary number to make sure we have some packets moving
            return False

        growth_rate = abs(curr - prev) / curr * 100
        logging.debug('growth is %f', growth_rate)

        if growth_rate == 0:
            return False  # Hack to deal with fact pushing packets every second but TSDB updated every minute
            # has the risk of never finishingress..

        return growth_rate < 0.05

    def bring_switch_full_load(self, dpid, port, size, outer_vlan=0, inner_vlan=0, vni=0, sleep=30):
        logging.info('Bringing switch to full load')
        done = False
        pkts_sent = 0
        while not done:
            self.send_packet_out(dpid, port, outer_vlan, inner_vlan, vni, size, 1)
            pkts_sent += 1
            logging.debug('Injected %i packets per port in total', pkts_sent)
            time.sleep(1)
            done = self.switch_at_peak_load()
        logging.info('Injected %i packets with size of %i for port %i, tired so gonna sleep for %i seconds',
                     pkts_sent, size, port, sleep)
        time.sleep(sleep)

    def prepare_snake_flows(self, dpid, size, outer_vlan=0, inner_vlan=0, vni=0):
        switch = self.environment.sw_by_dpid(dpid)
        flowmods = flows.flow_snake(dpid, switch.snake_start_port, switch.snake_end_port, 0)
        for flow in flowmods:
            self.add_flow(flow)
        self.time_metrics[-1].basic_flows_installed = datetime.utcnow()
        self.bring_switch_full_load(dpid, -1, size, outer_vlan, inner_vlan, vni)
        self.time_metrics[-1].traffic_injected = datetime.utcnow()


