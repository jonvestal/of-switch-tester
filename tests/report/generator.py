import os
import requests
from jinja2 import Environment, PackageLoader


class ReportGenerator:
    def __init__(self, scenario):
        self.scenario = scenario
        if not os.path.isdir('../report'):
            os.mkdir('../report')
        self.env = Environment(loader=PackageLoader('report', 'template'))

    def report(self):
        template = self.env.get_template('index.html')
        template.stream(packet_sizes=self.scenario.packet_sizes).dump('../report/index.html')

    def generate_graph(self, idx):
        time_metrics = self.scenario.time_metrics[idx]
        self.get_graph(idx, time_metrics.start, time_metrics.stop)

    def get_graph(self, idx, start, stop):
        fmt = "%Y/%m/%d-%H:%M:%S"

        url = "http://{0}:{1}/q?start={2}&end={3}&m=sum:rate:port.packets" \
              "&o=&m=sum:rate:port.bits&o=axis%20x1y2&yrange=[0:]&wxh=1833x760&style=linespoint&png" \
                  .format(self.scenario.environment.otsdb_host, self.scenario.environment.otsdb_port,
                          start.strftime(fmt), stop.strftime(fmt))
        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            with open('../report/%d.png' % idx, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
