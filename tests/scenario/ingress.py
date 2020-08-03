import logging

from constants import OFPP_IN_PORT
from openflow import flows
from scenario.model import Scenario


class IngressQnqVlanScenario(Scenario):

    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding ingress_qnq_vlan rules")
            for flow in flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, outer_vid=47):
                self.add_flow(flow)
            for flow in flows.flow_pop_vlan_and_push_new_vlans(sw.dpid, sw.snake_start_port,
                                                               OFPP_IN_PORT, outer_vid=47):
                self.add_flow(flow)


class IngressVlanScenario(Scenario):

    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding ingress_vlan rules")
            for flow in flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT):
                self.add_flow(flow)
            for flow in flows.flow_pop_vlan_and_push_new_vlans(sw.dpid, sw.snake_start_port, OFPP_IN_PORT):
                self.add_flow(flow)


class IngressQnqVxlanScenario(Scenario):

    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding ingress_qnq_vxlan rules")
            for flow in flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, outer_vid=47):
                self.add_flow(flow)
            for flow in flows.flow_pop_vxlan_and_push_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT, outer_vid=47):
                self.add_flow(flow)


class IngressVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding ingress_vxlan rules")
            for flow in flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT):
                self.add_flow(flow)
            for flow in flows.flow_pop_vxlan_and_push_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT):
                self.add_flow(flow)
