#!/usr/bin/env python

import argparse
import logging
import time

import yaml

from report.generator import ReportGenerator
from scenario import basic as basic
from scenario import ingress_egress as ingress
from scenario import transit as transit
from scenario import loop as loop

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
    'metadata': basic.MetadataScenario,
    'ingress-egress-qnq-vlan': ingress.IngressEgressQnqVlanScenario,
    'ingress-egress-qnq-vxlan': ingress.IngressEgressQnqVxlanScenario,
    'ingress-egress-vlan': ingress.IngressEgressVlanScenario,
    'ingress-egress-vxlan': ingress.IngressEgressVxlanScenario,
    'transit-vlan': transit.TransitVlanScenario,
    'transit-vxlan': transit.TransitVxlanScenario
}


def get_scenario(config):
    cls = clazz_map[config['name']]
    return cls(**config)


def main(config):
    max_runs = 1
    run_num = 0
    scenario = get_scenario(config)
    report_generator = ReportGenerator(scenario)
    try:
        while run_num < max_runs:
            for i in range(len(scenario.packet_sizes)):
                scenario.execute(run_num)
                report_generator.generate_graph(i)
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
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
    )
    config = get_args()
    main(config)
