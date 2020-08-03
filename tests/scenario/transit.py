import logging

from constants import OFPP_IN_PORT
from openflow import flows
from scenario.model import Scenario


class TransitVlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding transit_vlan rules")
            self.add_flow(flows.flow_transit_vlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT))
            self.add_flow(flows.flow_transit_vlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT))
            self.add_flow(flows.flow_vlan_push_pop(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                   'push', vid=48, priority=1500))


class TransitVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.packet_size)
            logging.info("Switch under full load adding transit_vxlan rules")

            self.add_flow(flows.flow_transit_vxlan(sw.dpid, sw.snake_end_port, OFPP_IN_PORT))
            self.add_flow(flows.flow_transit_vxlan(sw.dpid, sw.snake_start_port, OFPP_IN_PORT))
            self.add_flow(flows.flow_vxlan_push(sw.dpid, sw.snake_start_port, OFPP_IN_PORT,
                                                'push', vid=48, priority=1500))
