import logging
import time
from datetime import datetime

from oftester.openflow import basic_flows as flows
from oftester.scenario.model import Scenario


class PpsLoopScenario(Scenario):
    def run(self):
        for sw in self.environment.switches.values():
            timestamp = int(datetime.now().timestamp())
            self.time_metrics[-1].timestamps[timestamp] = "start"
            self.add_flow(flows.flow_loop_all_ports(sw.dpid, 0, 100))
            self.bring_switch_full_load(sw.dpid, -1,
                                        self.current_packet_size())


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

            self.bring_switch_full_load(sw.dpid, -1,
                                        self.current_packet_size())

            timestamp = int(datetime.now().timestamp())
            self.time_metrics[-1].timestamps[timestamp] = "start"
            table = 5
            while table > 0:
                self.add_flow(flows.flow_goto_table(sw.dpid, 0, table, 200))
                table_count = 5 - table + 1
                logging.info('Collecting data for tables = %i', table_count)
                time.sleep(self.collection_interval)
                timestamp = int(datetime.now().timestamp())
                self.time_metrics[-1].timestamps[timestamp] = \
                    "goto-table. Tables: " + str(table_count)
                table -= 1
