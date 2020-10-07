import os
import unittest
from datetime import datetime
from unittest.mock import Mock, mock_open, call, patch, PropertyMock

import requests
from plotly.graph_objs import Scatter

import oftester.report.generator as generator
import oftester.scenario.model as model


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        os.mkdir = Mock()

    def test_init(self):
        # when
        generator.OtsdbReportGenerator(Mock())
        # then
        os.mkdir.assert_called_once_with(generator.base_dir)

    def test_collect_data_otsdb(self):
        # given
        scenario_timestamp = model.ScenarioTimestamps()
        scenario_timestamp.start = datetime.utcnow()
        scenario_timestamp.stop = datetime.utcnow()
        scenario_attrs = {'time_metrics': [scenario_timestamp],
                          'get_current_packet_size_idx.return_value': 0,
                          'environment.otsdb_host': 'otsdb_host',
                          'environment.otsdb_port': 0,
                          'environment.otsdb_prefix': 'otsdb_prefix'}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.OtsdbReportGenerator(scenario)
        get_attrs = {'status_code': 200,
                     'iter_content.return_value': [1]}
        requests.get = Mock(return_value=Mock(**get_attrs))
        m_open = mock_open()

        # when
        with patch('oftester.report.generator.open', m_open, create=True):
            report_generator.collect_data()

        # then
        scenario.assert_has_calls([call.get_current_packet_size_idx(),
                                   call.get_current_packet_size_idx()])

        requests.get.assert_called_once()
        m_open.assert_has_calls([call('./reports/test_0.png', 'wb'),
                                 call().__enter__(),
                                 call().write(1),
                                 call().__exit__(None, None, None)])

    def test_report_otsdb(self):
        # given
        scenario_attrs = {'packet_sizes': [0, 1, 2]}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.OtsdbReportGenerator(scenario)
        template = Mock()
        report_generator.env.get_template = Mock(return_value=template)

        # when
        report_generator.report()

        # then
        report_generator.env.get_template.assert_has_calls(
            [call('otsdb_index.html')])
        template.assert_has_calls(
            [call.stream(name='test', packet_sizes=[0, 1, 2]),
             call.stream().dump('./reports/test.html')])

    def test_collect_data_plotly(self):
        # given
        scenario_timestamp = model.ScenarioTimestamps()
        scenario_timestamp.start = datetime.utcnow()
        scenario_timestamp.timestamps = dict()
        scenario_timestamp.stop = datetime.utcnow()
        scenario_attrs = {'time_metrics': [scenario_timestamp],
                          'get_current_packet_size_idx.return_value': 0,
                          'current_packet_size.return_value': 9000,
                          'environment.otsdb_host': 'otsdb_host',
                          'environment.otsdb_port': 0,
                          'environment.otsdb_prefix': 'otsdb_prefix'}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.PlotlyReportGenerator(scenario)
        get_attrs = {'status_code': 200,
                     'json.return_value': [{'test': 'test'}]}
        requests.get = Mock(return_value=Mock(**get_attrs))

        # when
        report_generator.collect_data()

        # then
        scenario.assert_has_calls([call.get_current_packet_size_idx(),
                                   call.current_packet_size()])
        requests.get.assert_called_once()

        self.assertEqual(report_generator.collected_data,
                         {9000: [{'test': 'test', 'timestamps': {}}]})

    def test_report_plotly(self):
        # given
        scenario_attrs = {'packet_sizes': [0, 1, 2],
                          'collection_interval': 30}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.PlotlyReportGenerator(scenario)
        report_generator.collected_data = {9000: [{'dps': {'1600411713': 1},
                                                   'metric': 'metric',
                                                   'timestamps': {}}]}
        fig = Mock(**{'to_html.return_value': 'test'})
        m_subplots = Mock(return_value=fig)
        template = Mock()
        report_generator.env.get_template = Mock(return_value=template)
        m_open = mock_open()

        # when
        with patch('oftester.report.generator.open', m_open, create=True):
            with patch('oftester.report.generator.make_subplots',
                       m_subplots, create=True):
                report_generator.report()

        # then
        m_subplots.assert_has_calls([call(specs=[[{'secondary_y': True}]])])
        fig.assert_has_calls([call.add_trace(Scatter({
            'name': 'metric', 'x': [datetime(2020, 9, 18, 10, 48, 33)],
            'y': [1]
        }), secondary_y=True),
            call.update_yaxes(title_text='metric y-axis', secondary_y=True),
            call.update_layout(title_text='Packet size: 9000'),
            call.to_html(full_html=False, include_plotlyjs='cdn',
                         default_height='100vh')])

        report_generator.env.get_template.assert_has_calls(
            [call('plotly_index.html')])
        m_open.assert_has_calls(
            [call('./reports/test.json', 'wb'),
             call().__enter__(),
             call().write(b'{"9000": [{"dps": {"1600411713": 1}, '
                          b'"metric": "metric", '
                          b'"timestamps": {}}]}'),
             call().__exit__(None, None, None)])
        template.assert_has_calls(
            [call.stream(name='test', figures=['test']),
             call.stream().dump('./reports/test-plotly.html')])

    def test_collect_data_plotly_aggr(self):
        # given
        scenario_timestamp = model.ScenarioTimestamps()
        scenario_timestamp.start = datetime.utcnow()
        scenario_timestamp.timestamps = dict()
        scenario_timestamp.stop = datetime.utcnow()
        scenario_attrs = {'time_metrics': [scenario_timestamp],
                          'get_current_packet_size_idx.return_value': 0,
                          'current_packet_size.return_value': 9000,
                          'environment.otsdb_host': 'otsdb_host',
                          'environment.otsdb_port': 0,
                          'environment.otsdb_prefix': 'otsdb_prefix'}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.PlotlyAggregatedReportGenerator(scenario)
        get_attrs = {'status_code': 200,
                     'json.return_value': [{'test': 'test'}]}
        requests.get = Mock(return_value=Mock(**get_attrs))

        # when
        report_generator.collect_data()

        # then
        scenario.assert_has_calls([call.get_current_packet_size_idx(),
                                   call.current_packet_size()])
        requests.get.assert_called_once()

        self.assertEqual(report_generator.collected_data,
                         {9000: [{'test': 'test', 'timestamps': {}}]})

    def test_report_plotly_aggr(self):
        # given
        scenario_attrs = {'packet_sizes': [0, 1, 2],
                          'environment.otsdb_prefix': 'otsdb_prefix',
                          'collection_interval': 30}
        scenario = Mock(**scenario_attrs)
        type(scenario).name = PropertyMock(return_value='test')
        report_generator = generator.PlotlyAggregatedReportGenerator(scenario)
        report_generator.collected_data = {9000: [{'dps': {'1600411713': 1},
                                                   'metric': 'metric',
                                                   'timestamps': {}}]}
        fig = Mock(**{'to_html.return_value': 'test'})
        m_subplots = Mock(return_value=fig)
        template = Mock()
        report_generator.env.get_template = Mock(return_value=template)
        m_open = mock_open()

        # when
        with patch('oftester.report.generator.open', m_open, create=True):
            with patch('oftester.report.generator.make_subplots',
                       m_subplots, create=True):
                report_generator.report()

        # then
        m_subplots.assert_has_calls([call(specs=[[{'secondary_y': True}]]),
                                     call(), call()])
        fig.assert_has_calls([call.add_trace(Scatter({
            'name': 'metric', 'x': [datetime(2020, 9, 18, 10, 48, 33)],
            'y': [1]
        }), secondary_y=True),
            call.update_yaxes(title_text='metric y-axis', secondary_y=True),
            call.update_layout(title_text='Packet size: 9000'),
            call.to_html(full_html=False, include_plotlyjs='cdn',
                         default_height='100vh'),
            call.update_layout(title_text='Metric: otsdb_prefix.port.bits'),
            call.to_html(full_html=False, include_plotlyjs='cdn',
                         default_height='100vh'),
            call.update_layout(title_text='Metric: otsdb_prefix.port.packets'),
            call.to_html(full_html=False, include_plotlyjs='cdn',
                         default_height='100vh')])

        report_generator.env.get_template.assert_has_calls(
            [call('plotly_index.html'),
             call('plotly_index.html')])
        m_open.assert_has_calls(
            [call('./reports/test.json', 'wb'),
             call().__enter__(),
             call().write(b'{"9000": [{"dps": {"1600411713": 1}, '
                          b'"metric": "metric", '
                          b'"timestamps": {}}]}'),
             call().__exit__(None, None, None)])
        template.assert_has_calls(
            [call.stream(name='test', figures=['test']),
             call.stream().dump('./reports/test-plotly.html'),
             call.stream(name='test', figures=['test', 'test']),
             call.stream().dump('./reports/test-plotly-aggr.html')])


if __name__ == '__main__':
    unittest.main()
