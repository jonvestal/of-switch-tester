import logging
import time

from oftester.openflow import basic_flows as flows
from oftester.scenario.model import Scenario


class PpsLoopScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            self.add_flow(flows.flow_loop_all_ports(sw.dpid, 0, 100))
            self.bring_switch_full_load(sw.dpid, -1, self.current_packet_size())


class GoToTableScenario(Scenario):
    def run(self):
        logging.info('Performing GoTo Table test')
        for sw in self.environment.switches.values():
            self.add_flow(flows.flow_loop_all_ports(sw.dpid, 0, 100))
            self.add_flow(flows.flow_loop_all_ports(sw.dpid, 5, 100))
            self.add_flow(flows.flow_goto_table(sw.dpid, 1, 2, 100))
            self.add_flow(flows.flow_goto_table(sw.dpid, 2, 3, 100))
            self.add_flow(flows.flow_goto_table(sw.dpid, 3, 4, 100))
            self.add_flow(flows.flow_goto_table(sw.dpid, 4, 5, 100))

            self.bring_switch_full_load(sw.dpid, -1, self.current_packet_size())

            table = 5
            while table > 0:
                self.add_flow(flows.flow_goto_table(sw.dpid, 0, table, 200))
                logging.info('Collecting data for tables = %i', 5 - table + 1)
                time.sleep(self.collection_interval)
                table -= 1
