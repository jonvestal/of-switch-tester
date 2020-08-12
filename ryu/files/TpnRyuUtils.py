import json

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import dpset
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import dpid as dpid_lib
from ryu.lib.packet import ethernet, ipv4, udp, packet, vlan, vxlan
from ryu.ofproto import ether, inet
from ryu.ofproto import ofproto_v1_3

SWITCHID_PATTERN = dpid_lib.DPID_PATTERN + r'|all'
VLANID_PATTERN = r'[0-9]{1,4}|all'
REQUIREMENTS = {'switchid': SWITCHID_PATTERN,
                'vlanid': VLANID_PATTERN}

DL_DST = '11:22:33:44:55:66'
DL_SRC = '66:55:44:33:22:11'
IP_SRC = '1.1.1.1'
IP_DST = '2.2.2.2'
IP_PROTO = inet.IPPROTO_UDP

pipeline_tester_instance_name = "PipelineTesterInstance"


def make_packet(pkt_size, outer_vlan=0, inner_vlan=0, vni=0):
    dl_type = ether.ETH_TYPE_IP
    if outer_vlan or inner_vlan:
        dl_type = ether.ETH_TYPE_8021Q
    e = ethernet.ethernet(DL_DST, DL_SRC, dl_type)
    i = ipv4.ipv4(total_length=0, src=IP_SRC, dst=IP_DST, proto=IP_PROTO, ttl=1)
    dst_udp_port = 10000
    if vni:
        dst_udp_port = 4789
    u = udp.udp(src_port=5000, dst_port=dst_udp_port)

    outer_len = 0
    outer_tag = None
    if outer_vlan:
        outer_tag = vlan.vlan(vid=outer_vlan, ethertype=ether.ETH_TYPE_8021Q, cfi=1)
        outer_len = len(outer_tag)

    inner_len = 0
    inner_tag = None
    if inner_vlan:
        inner_tag = vlan.vlan(vid=inner_vlan, ethertype=ether.ETH_TYPE_8021Q, cfi=1)
        inner_len = len(inner_tag)
    vxlan_len = 0
    vxlan_tag = None
    if vni:
        vxlan_tag = vxlan.vxlan(vni)
        vxlan_len = len(vxlan_tag)

    payload_size = pkt_size - (len(e) + len(i) + len(u) + inner_len + outer_len + vxlan_len)
    payload = bytearray(payload_size if payload_size > 0 else 0)

    p = packet.Packet()
    p.add_protocol(e)
    if outer_tag:
        p.add_protocol(outer_tag)
    if inner_tag:
        p.add_protocol(inner_tag)
    p.add_protocol(i)
    p.add_protocol(u)
    if vxlan_tag:
        p.add_protocol(vxlan_tag)
    p.add_protocol(payload)

    return p


class TpnRyuUtils(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
                'dpset': dpset.DPSet,
                'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(TpnRyuUtils, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        wsgi.register(PipelineTesterController, {pipeline_tester_instance_name: self})

    def send_packet(self, dpid, pkt, port):
        dp = self.dpset.get(dpid)
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        port = ofp.OFPP_FLOOD if port < 0 else port
        actions = [ofp_parser.OFPActionOutput(port)]
        req = ofp_parser.OFPPacketOut(dp,
                                      in_port=ofp.OFPP_CONTROLLER,
                                      buffer_id=ofp.OFP_NO_BUFFER,
                                      actions=actions,
                                      data=pkt)
        dp.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_event_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.logger.info('register datapath: %016x', datapath.id)
        elif ev.state == DEAD_DISPATCHER:
            self.logger.info('unregister datapath: %016x', datapath.id)
        else:
            self.logger.error("Somehow %016x unregistered with us but was never registered", datapath.id)


class PipelineTesterController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(PipelineTesterController, self).__init__(req, link, data, **config)
        self.pipeline_tester_app = data[pipeline_tester_instance_name]

    @route('tester', '/tpn/packet_out/{switchid}', methods=['POST'])
    def send_packetout(self, req, **kwargs):
        app = self.pipeline_tester_app
        if req.content_type == 'application/json':
            payload = json.loads(req.body)
        else:
            raise ValueError("Not valid payload")

        switchid = int(kwargs['switchid'], 0)
        pkt_size = payload['pkt_size']
        outer_vlan = payload['outer_vlan']
        inner_vlan = payload['inner_vlan']
        vni = payload['vni']
        port = payload['port']

        count = 1
        if 'count' in payload:
            count = payload['count']

        p = make_packet(pkt_size, outer_vlan, inner_vlan, vni)
        while count > 0:
            app.send_packet(switchid, p, port)
            count -= 1
