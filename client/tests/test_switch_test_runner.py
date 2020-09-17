import os
import time
import unittest
from unittest.mock import Mock, call

import oftester.report.generator as generator
import oftester.scenario.model as model
import oftester.switch_test_runner as switch_test_runner


class TestSwitchTestRunner(unittest.TestCase):

    def setUp(self):
        self.config = {
            'names': list(switch_test_runner.clazz_map.keys()),
            'packet_sizes': ['100', '500', '1500', '4000', '9000'],
            'collection_interval': 1,
            'environment': {
                'otsdb_host': 'localhost',
                'otsdb_port': 4242,
                'otsdb_prefix': 'oftester',
                'ryu_host': 'localhost',
                'ryu_port': 8080,
                'reports': 'plotly',
                'switches': [{
                    'dpid': '00:00:00:22:33:55:66:77',
                    'snake_start_port': 5,
                    'snake_end_port': 28,
                    'ingress_port': 3,
                    'egress_port': 4
                }]
            }
        }
        self.names_count = len(self.config['names'])
        self.packet_sizes_count = len(self.config['packet_sizes'])

        time.sleep = Mock()
        os.mkdir = Mock()

        self.scenario_execute = model.Scenario.execute
        self.scenario_cleanup_switch = model.Scenario.cleanup_switch
        self.plotly_collect_data = generator.PlotlyReportGenerator.collect_data
        self.scenario_report = generator.PlotlyReportGenerator.report
        self.get_scenarios = switch_test_runner.get_scenarios
        self.get_report_generator = switch_test_runner.get_report_generator

    def tearDown(self):
        model.Scenario.execute = self.scenario_execute
        model.Scenario.cleanup_switch = self.scenario_cleanup_switch
        generator.PlotlyReportGenerator.collect_data = self.plotly_collect_data
        generator.PlotlyReportGenerator.report = self.scenario_report
        switch_test_runner.get_scenarios = self.get_scenarios
        switch_test_runner.get_report_generator = self.get_report_generator

    def test_main(self):
        model.Scenario.execute = Mock()
        model.Scenario.cleanup_switch = Mock()
        generator.PlotlyReportGenerator.collect_data = Mock()
        generator.PlotlyReportGenerator.report = Mock()

        switch_test_runner.main(self.config)

        self.assertEqual(model.Scenario.execute.call_count, self.names_count * self.packet_sizes_count)
        self.assertEqual(generator.PlotlyReportGenerator.collect_data.call_count,
                         self.names_count * self.packet_sizes_count)
        self.assertEqual(generator.PlotlyReportGenerator.report.call_count, self.names_count)

    def test_main_wrong_scenario_name(self):
        self.config['names'] = ['test']
        with self.assertRaises(KeyError):
            switch_test_runner.main(self.config)

    def test_tester_calls(self):
        attrs = {'has_next_packet_size.side_effect': [True, False]}
        scenario = Mock(**attrs)
        switch_test_runner.get_scenarios = Mock(return_value=[scenario])
        report_generator = Mock()
        switch_test_runner.get_report_generator = Mock(return_value=report_generator)

        switch_test_runner.main(self.config)

        scenario.assert_has_calls([call.has_next_packet_size(),
                                   call.next_packet_size(),
                                   call.execute(),
                                   call.has_next_packet_size(),
                                   call.cleanup_switch()], any_order=False)

        report_generator.assert_has_calls([call.collect_data(), call.report()], any_order=False)

        switch_test_runner.get_scenarios.assert_has_calls([call(self.config)])
        switch_test_runner.get_report_generator.assert_has_calls([call(scenario)])

    def test_tester_calls_with_generator(self):
        scenario_timestamp = model.ScenarioTimestamps()
        scenario_timestamp.start = 1
        scenario_timestamp.stop = 2
        attrs = {'has_next_packet_size.side_effect': [True, False], 'environment.reports': 'plotly',
                 'time_metrics': [scenario_timestamp], 'get_current_packet_size_idx.return_value': 0}
        scenario = Mock(**attrs)
        switch_test_runner.get_scenarios = Mock(return_value=[scenario])
        generator.PlotlyReportGenerator.get_points = Mock()
        generator.PlotlyReportGenerator.report = Mock()

        switch_test_runner.main(self.config)

        scenario.assert_has_calls([call.has_next_packet_size(),
                                   call.next_packet_size(),
                                   call.execute(),
                                   call.get_current_packet_size_idx(),
                                   call.current_packet_size(),
                                   call.has_next_packet_size(),
                                   call.cleanup_switch()], any_order=False)

        switch_test_runner.get_scenarios.assert_has_calls([call(self.config)])


if __name__ == '__main__':
    unittest.main()
