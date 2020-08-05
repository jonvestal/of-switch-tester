import os
import requests
from jinja2 import Environment, PackageLoader

base_dir = './reports'


class ReportGenerator:
    def __init__(self, scenario):
        self.scenario = scenario
        if not os.path.isdir(base_dir):
            os.mkdir(base_dir)
        self.env = Environment(loader=PackageLoader('oftester.report', 'template'))

    def report(self):
        template = self.env.get_template('index.html')
        template.stream(name=self.scenario.name,
                        packet_sizes=self.scenario.packet_sizes).dump(base_dir + '/' + self.scenario.name + '.html')

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
            with open(base_dir + '/%s_%d.png' % (self.scenario.name, idx), 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
