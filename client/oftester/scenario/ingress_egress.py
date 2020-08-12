import logging

from oftester.constants import OFPP_IN_PORT
from oftester.openflow import pipeline_flows
from oftester.scenario.model import Scenario


class IngressEgressQnqVlanScenario(Scenario):

    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46, inner_vlan=47)
            logging.info('Switch under full load adding ingress_egress_qnq_vlan rules')
            for flow in pipeline_flows.flow_egress_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                        outer_vid=46, inner_vid=47, priority=2000):
                self.add_flow(flow)
            for flow in pipeline_flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT,
                                                         outer_vid=46, inner_vid=47, priority=2000):
                self.add_flow(flow)


class IngressEgressVlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46)
            logging.info('Switch under full load adding ingress_egress_vlan rules')
            for flow in pipeline_flows.flow_egress_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                        outer_vid=46, inner_vid=None, priority=2000):
                self.add_flow(flow)

            for flow in pipeline_flows.flow_ingress_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, outer_vid=46,
                                                         inner_vid=None, priority=2000):
                self.add_flow(flow)


class IngressEgressQnqVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46, inner_vlan=47)
            logging.info('Switch under full load adding ingress_egress_qnq_vxlan rules')
            for flow in pipeline_flows.flow_egress_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                         outer_vid=46, inner_vid=47, priority=2000):
                    self.add_flow(flow)
            for flow in pipeline_flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT,
                                                          outer_vid=46, inner_vid=47, priority=2000):
                self.add_flow(flow)


class IngressEgressVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(), outer_vlan=46)
            logging.info('Switch under full load adding ingress_egress_vxlan rules')
            for flow in pipeline_flows.flow_egress_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT, outer_vid=46,
                                                         inner_vid=None, priority=2000):
                self.add_flow(flow)
            for flow in pipeline_flows.flow_ingress_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT, outer_vid=46,
                                                          inner_vid=None, priority=2000):
                self.add_flow(flow)
