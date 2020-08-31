import logging

from oftester.constants import OFPP_IN_PORT
from oftester.openflow import basic_flows
from oftester.openflow import pipeline_flows
from oftester.scenario.model import Scenario
from oftester.openflow import groups


# This scenario doesn't work until Noviflow fixes the bug related to VxLAN header and metadata matching.
class ConnectedDevicesVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46, inner_vlan=47)
            logging.info('Switch under full load adding connected_devices_vxlan rules')
            for flow in pipeline_flows.flow_egress_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                         outer_vid=46, inner_vid=47, priority=2000):
                self.add_flow(flow)
            self.add_flow(basic_flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT, 'push',
                                                         outer_vid=46, inner_vid=47, priority=1500, table_id=4))
            for flow in pipeline_flows.flows_connected_devices_with_vxlan(sw.dpid, sw.snake_end_port,
                                                                          OFPP_IN_PORT, outer_vid=46,
                                                                          inner_vid=47, priority=2000):
                self.add_flow(flow)


class ConnectedDevicesVlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46, inner_vlan=47)
            logging.info('Switch under full load adding connected_devices_vlan rules')
            for flow in pipeline_flows.flow_egress_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                        outer_vid=46, inner_vid=47, priority=2000):
                self.add_flow(flow)
            for flow in pipeline_flows.flows_connected_devices_with_vlan(sw.dpid, sw.snake_end_port,
                                                                         OFPP_IN_PORT, outer_vid=46,
                                                                         inner_vid=47, priority=2000):
                self.add_flow(flow)


class RtlScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            eth_dst = 'aa:bb:cc:dd:ee:ff'
            eth_type = 2048
            ip_proto = 17
            udp_dst = 6000
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(),
                                     eth_dst=eth_dst, eth_type=eth_type, ip_proto=ip_proto, udp_dst_port=udp_dst)
            logging.info('Switch under full load adding rtl rules')
            group = groups.group_rtl(sw.dpid, sw.snake_end_port - 2, sw.snake_end_port, mac=eth_dst, udp_port=udp_dst)
            self.add_group(group)
            self.add_flow(pipeline_flows.flow_rtl(sw.dpid, sw.snake_start_port, eth_dst=eth_dst, eth_type=eth_type,
                                                  ip_proto=ip_proto, udp_dst_port=udp_dst, priority=2000))
