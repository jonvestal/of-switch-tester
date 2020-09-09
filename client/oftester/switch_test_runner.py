#!/usr/bin/env python

import argparse
import logging
import time

import yaml

from oftester.report import generator
from oftester.scenario import basic as basic
from oftester.scenario import ingress_egress as ingress
from oftester.scenario import loop as loop
from oftester.scenario import multicast as multicast
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
    'multicast-goto-table': basic.MulticastGotoTableScenario,
    'multicast-group': basic.MulticastGroupScenario,
    'ingress-egress-qnq-vlan': ingress.IngressEgressQnqVlanScenario,
    'ingress-egress-qnq-vxlan': ingress.IngressEgressQnqVxlanScenario,
    'ingress-egress-vlan': ingress.IngressEgressVlanScenario,
    'ingress-egress-vxlan': ingress.IngressEgressVxlanScenario,
    'transit-vlan': transit.TransitVlanScenario,
    'transit-vxlan': transit.TransitVxlanScenario,
    'connected-devices-vxlan': multicast.ConnectedDevicesVxlanScenario,
    'connected-devices-vlan': multicast.ConnectedDevicesVlanScenario,
    'rtl': multicast.RtlScenario
}

report_generator_map = {
    'plotly': generator.PlotlyReportGenerator,
    'plotly-aggregated': generator.PlotlyAggregatedReportGenerator,
    'otsdb': generator.OtsdbReportGenerator
}


def get_scenarios(config):
    scenarios = []
    names = config['names']
    del config['names']
    for name in names:
        cls = clazz_map[name]
        scenarios.append(cls(name=name, **config))
    return scenarios


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
    scenarios = get_scenarios(config)
    for scenario in scenarios:
        report_generator = get_report_generator(scenario)
        try:
            while scenario.has_next_packet_size():
                scenario.next_packet_size()
                scenario.execute()
                report_generator.collect_data()
                time.sleep(10)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.exception(e)
        scenario.cleanup_switch()
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
