#!/usr/bin/env python3


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
import potsdb


class TpnBaselinerStats(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TpnBaselinerStats, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.collector_thread = hub.spawn(self.run_stats_collector)
        self.metrics = potsdb.Client('localhost')

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_event_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath not in self.datapaths:
                self.logger.info('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath in self.datapaths:
                self.logger.info('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
            else:
                self.logger.error("Somehow %016x unregistered with us but was never registered", datapath.id)
        else:
            self.logger.error("This shouldn't have happened as not capturing %s", ev.state)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
            self.metrics.send('flow.packets',
                              stat.packet_count,
                              dpid=ev.msg.datapath.id,
                              cookie='xxx')
            self.metrics.send('flow.bits',
                              stat.byte_count * 8,
                              dpid=ev.msg.datapath.id,
                              cookie='xxx')

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=lambda x: x.port_no):
            self.logger.info('%016x %8d %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            self.metrics.send('port.packets',
                              stat.rx_packets,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='rx')
            self.metrics.send('port.packets',
                              stat.tx_packets,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='tx')
            self.metrics.send('port.bits',
                              stat.rx_bytes * 8,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='rx')
            self.metrics.send('port.bits',
                              stat.tx_bytes * 8,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='tx')
            self.metrics.send('port.errors',
                              stat.rx_errors,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='rx')
            self.metrics.send('port.errors',
                              stat.tx_errors,
                              dpid=ev.msg.datapath.id,
                              port=stat.port_no,
                              direction='tx')

    def request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    def run_stats_collector(self):
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(10)
