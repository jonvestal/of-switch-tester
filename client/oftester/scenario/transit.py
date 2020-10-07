import logging
from datetime import datetime

from oftester.constants import OFPP_IN_PORT
from oftester.openflow import pipeline_flows
from oftester.scenario.model import Scenario


class TransitVlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(),
                                     outer_vlan=48)
            timestamp = int(datetime.now().timestamp())
            self.time_metrics[-1].timestamps[timestamp] = "start"
            logging.info('Switch under full load adding transit_vlan rules')
            for flow in pipeline_flows.flow_transit_vlan(sw.dpid,
                                                         sw.snake_end_port,
                                                         OFPP_IN_PORT):
                self.add_flow(flow)
            for flow in pipeline_flows.flow_transit_vlan(sw.dpid,
                                                         sw.snake_start_port,
                                                         OFPP_IN_PORT):
                self.add_flow(flow)


class TransitVxlanScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.prepare_snake_flows(sw.dpid, self.current_packet_size(),
                                     vni=48)
            timestamp = int(datetime.now().timestamp())
            self.time_metrics[-1].timestamps[timestamp] = "start"
            logging.info('Switch under full load adding transit_vxlan rules')

            for flow in pipeline_flows.flow_transit_vxlan(
                    sw.dpid, sw.snake_end_port, OFPP_IN_PORT, vni=48):
                self.add_flow(flow)
            for flow in pipeline_flows.flow_transit_vxlan(
                    sw.dpid, sw.snake_start_port, OFPP_IN_PORT, vni=48):
                self.add_flow(flow)
