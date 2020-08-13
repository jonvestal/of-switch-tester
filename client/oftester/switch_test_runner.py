#!/usr/bin/env python

import argparse
import logging
import time

import yaml

from oftester.report import generator
from oftester.scenario import basic as basic
from oftester.scenario import ingress_egress as ingress
from oftester.scenario import loop as loop
from oftester.scenario import transit as transit

clazz_map = {
    'pps': basic.PpsScenario,
    'pps-loop': loop.PpsLoopScenario,
    'goto-table': loop.GoToTableScenario,
    'vlan': basic.VlanScenario,
    'vlan-header': basic.VlanScenarioShort,
    'vxlan': basic.VxlanScenario,
    'vxlan-header': basic.VxlanScenarioShort,
    'swap': basic.SwapScenario,
    'copy': basic.CopyScenario,
    'rx-timestamp': basic.RxTimestampScenario,
    'tx-timestamp': basic.TxTimestampScenario,
    'metadata': basic.MetadataScenario,
    'ingress-egress-qnq-vlan': ingress.IngressEgressQnqVlanScenario,
    'ingress-egress-qnq-vxlan': ingress.IngressEgressQnqVxlanScenario,
    'ingress-egress-vlan': ingress.IngressEgressVlanScenario,
    'ingress-egress-vxlan': ingress.IngressEgressVxlanScenario,
    'transit-vlan': transit.TransitVlanScenario,
    'transit-vxlan': transit.TransitVxlanScenario
}

report_generator_map = {
    'plotly': generator.PlotlyReportGenerator,
    'otsdb': generator.OtsdbReportGenerator
}


def get_scenario(config):
    cls = clazz_map[config['name']]
    return cls(**config)


def get_report_generator(scenario):
    report_generator = report_generator_map[scenario.environment.reports]
    return report_generator(scenario)


def main(config=None):
    if not config:
        logging.basicConfig(
            format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
            level=logging.INFO
        )
        config = get_args()
    max_runs = 1
    run_num = 0
    scenario = get_scenario(config)
    report_generator = get_report_generator(scenario)
    try:
        while run_num < max_runs:
            for i in range(len(scenario.packet_sizes)):
                packet_size = scenario.current_packet_size()
                scenario.execute(run_num)
                report_generator.collect_data(i, packet_size)
                time.sleep(10)
            run_num += 1
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(e)
    scenario.delete_all_flows()
    report_generator.report()


def _parsecmdline():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('scenario', action='store', help='scenario.yaml file')
    return parser.parse_args()


def get_args():
    args = _parsecmdline()
    with open(args.scenario) as f:
        return yaml.safe_load(f)


if __name__ == '__main__':
    main()
