import logging

from constants import OFPP_IN_PORT
from openflow import flows
from scenario.model import Scenario


class IngressEgressQnqVlanScenario(Scenario):

    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size())
            logging.info("Switch under full load adding ingress_egress_qnq_vlan rules")
            for flow in flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT,
                                                inner_vid=46, outer_vid=47, priority=2000):
                self.add_flow(flow)
            self.add_flow(flows.flow_egress_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                 inner_vid=46, outer_vid=47, priority=2000))
            self.add_flow(flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                   'push', vid=46, outer_vid=47, priority=1500))


class IngressEgressVlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size())
            logging.info("Switch under full load adding ingress_egress_vlan rules")
            for flow in flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, inner_vid=46, priority=2000):
                self.add_flow(flow)
            self.add_flow(flows.flow_egress_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                 inner_vid=46, priority=2000))
            self.add_flow(flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                   'push', vid=46, priority=1500))


class IngressEgressQnqVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size())
            logging.info("Switch under full load adding ingress_egress_qnq_vxlan rules")
            for flow in flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT,
                                                 inner_vid=46, outer_vid=47, priority=2000):
                self.add_flow(flow)
            self.add_flow(flows.flow_egress_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                  inner_vid=46, outer_vid=47, priority=2000))
            self.add_flow(flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                   'push', vid=46, outer_vid=47, priority=1500))


class IngressEgressVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size())
            logging.info("Switch under full load adding ingress_egress_vxlan rules")
            for flow in flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, inner_vid=46, priority=2000):
                self.add_flow(flow)
            self.add_flow(flows.flow_egress_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                  inner_vid=46, priority=2000))
            self.add_flow(flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                   'push', vid=46, priority=1500))
