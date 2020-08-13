import datetime
import logging
import os
from abc import abstractmethod, ABC

import plotly.graph_objects as go
import requests
from jinja2 import Environment, PackageLoader
from plotly.subplots import make_subplots

base_dir = './reports'


class ReportGenerator(ABC):
    def __init__(self, scenario):
        self.scenario = scenario
        if not os.path.isdir(base_dir):
            os.mkdir(base_dir)
        self.env = Environment(loader=PackageLoader('oftester.report', 'template'))

    @abstractmethod
    def report(self):
        pass

    @abstractmethod
    def collect_data(self, idx, packet_size):
        pass


class OtsdbReportGenerator(ReportGenerator):
    def report(self):
        template = self.env.get_template('otsdb_index.html')
        template.stream(name=self.scenario.name,
                        packet_sizes=self.scenario.packet_sizes).dump(base_dir + '/' + self.scenario.name + '.html')

    def collect_data(self, idx, packet_size):
        time_metrics = self.scenario.time_metrics[idx]
        self.get_graph(idx, time_metrics.start, time_metrics.stop)

    def get_graph(self, idx, start, stop):
        fmt = "%Y/%m/%d-%H:%M:%S"

        url = "http://{0}:{1}/q?start={2}&end={3}&m=sum:rate:port.packets" \
              "&o=&m=sum:rate:port.bits&o=axis%20x1y2&ylabel=y&yrange=[0:]&wxh=1833x760&style=linespoint&png" \
                  .format(self.scenario.environment.otsdb_host, self.scenario.environment.otsdb_port,
                          start.strftime(fmt), stop.strftime(fmt))
        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            with open(base_dir + '/%s_%d.png' % (self.scenario.name, idx), 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)


class PlotlyReportGenerator(ReportGenerator):
    def __init__(self, scenario):
        super(PlotlyReportGenerator, self).__init__(scenario)
        self.collected_data = dict()

    def report(self):
        figures = []
        for packet_size in self.collected_data:
            fig = self.make_figure(packet_size, self.collected_data[packet_size])
            figures.append(fig.to_html(full_html=False, include_plotlyjs='cdn', default_height='100vh'))

        template = self.env.get_template('plotly_index.html')
        template.stream(name=self.scenario.name,
                        figures=figures).dump(base_dir + '/' + self.scenario.name + '.html')
        logging.info("Report for %s scenario has been created", self.scenario.name)

    def collect_data(self, idx, packet_size):
        time_metrics = self.scenario.time_metrics[idx]
        self.get_points(time_metrics.start, time_metrics.stop, packet_size)

    def get_points(self, start, stop, packet_size):
        fmt = "%Y/%m/%d-%H:%M:%S"

        url = "http://{0}:{1}/api/query?start={2}&end={3}&m=sum:rate:port.packets" \
              "&o=&m=sum:rate:port.bits&o=axis%20x1y2&ylabel=y&yrange=[0:]" \
                  .format(self.scenario.environment.otsdb_host, self.scenario.environment.otsdb_port,
                          start.strftime(fmt), stop.strftime(fmt))
        resp = requests.get(url)
        if resp.status_code == 200:
            self.collected_data[packet_size] = resp.json()
            logging.info("Stored data for packet size: %i", packet_size)

    @staticmethod
    def make_figure(packet_size, data):
        fig = make_subplots(specs=[[{'secondary_y': True}]])

        i = 0
        for d in data:
            secondary_y = i % 2 == 0
            i += 1
            x_axis = list(map(lambda x: datetime.datetime.fromtimestamp(int(x)), list(d['dps'].keys())))
            fig.add_trace(go.Scatter(x=x_axis, y=list(d['dps'].values()), name=d['metric']), secondary_y=secondary_y)
            fig.update_yaxes(title_text=d['metric'] + ' y-axis', secondary_y=secondary_y)

        fig.update_layout(title_text='Packet size: ' + str(packet_size))

        return fig


class PlotlyAggregatedReportGenerator(PlotlyReportGenerator):

    def report(self):
        figures = []
        fig = self.make_figure('port.bits')
        figures.append(fig.to_html(full_html=False, include_plotlyjs='cdn', default_height='100vh'))
        fig = self.make_figure('port.packets')
        figures.append(fig.to_html(full_html=False, include_plotlyjs='cdn', default_height='100vh'))

        template = self.env.get_template('plotly_index.html')
        template.stream(name=self.scenario.name,
                        figures=figures).dump(base_dir + '/' + self.scenario.name + '.html')
        logging.info("Report for %s scenario has been created", self.scenario.name)

    def make_figure(self, metric):
        fig = make_subplots()
        for packet_size in self.collected_data:
            for d in self.collected_data[packet_size]:
                if d['metric'] == metric:
                    timestamps = list(d['dps'].keys())
                    start_time = int(timestamps[0])
                    x_axis = list(map(lambda x: int(x) - start_time, timestamps))
                    fig.add_trace(go.Scatter(x=x_axis, y=list(d['dps'].values()), name=str(packet_size)))

        fig.update_layout(title_text='Metric: ' + metric)
        return fig
