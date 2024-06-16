#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2024 Amirali.T
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import atexit
import argparse
from jtop import jtop, JtopException
from prometheus_client.core import InfoMetricFamily, GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server


class JetsonNanoCollector(object):
    def __init__(self):
        atexit.register(self.cleanup)

        self._jetson = jtop()
        self._jetson.start()
        if not self._jetson.ok():
            raise JtopException("Jtop not available")

    def cleanup(self):
        print("Closing jetson-stats connection...")
        self._jetson.close()

    def collect(self):
        yield from self.collect_board_info()
        yield from self.collect_system_uptime()
        yield from self.collect_cpu_usage()
        yield from self.collect_gpu_usage()
        yield from self.collect_ram_usage()
        yield from self.collect_disk_usage()
        yield from self.collect_fan_usage()
        yield from self.collect_sensor_temperatures()
        yield from self.collect_power_usage()
        yield from self.collect_voltages()
        yield from self.collect_network_interfaces()

    def collect_board_info(self):
        try:
            i = InfoMetricFamily('jetson_board', 'Board sys info')
            i.add_metric([],{
                'machine': self._jetson.board['platform']['Machine'],
                'distribution': self._jetson.board['platform']['Distribution'],
                'release': self._jetson.board['platform']['Release'],
                'jetpack': self._jetson.board['hardware']['Jetpack'], 
                'l4t': self._jetson.board['hardware']['L4T'],
                'module': self._jetson.board['hardware']['Module'],
                'type': self._jetson.board['hardware']['Model'],
                'codename': self._jetson.board['hardware']['Codename'],
                'soc': self._jetson.board['hardware']['SoC'],
                'cuda_arch_bin': self._jetson.board['hardware']['CUDA Arch BIN'],
                'serial_number': self._jetson.board['hardware']['Serial Number'],
                'nvpmode': self._jetson.nvpmodel.name
            })
            yield i
        except JtopException as e:
            print("Jtop Error collecting board info: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_system_uptime(self):
        try:
            g = GaugeMetricFamily('jetson_uptime', 'System uptime', labels=['uptime'])
            days = self._jetson.uptime.days
            seconds = self._jetson.uptime.seconds
            hours = seconds // 3600
            minutes = (seconds // 60) % 60
            g.add_metric(['days'], days)
            g.add_metric(['hours'], hours)
            g.add_metric(['minutes'], minutes)
            yield g
        except JtopException as e:
            print("Jtop Error collecting system uptime: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_cpu_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_cpu', 'CPU % schedutil', labels=['cpu'])
            for i in range(len(self._jetson.cpu['cpu'])):
                g.add_metric(['cpu_' + str(i + 1)], 100.0 - self._jetson.cpu['cpu'][i]['idle'])

            g.add_metric(['cpu_total'], 100.0 - self._jetson.cpu['total']['idle'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting CPU usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_gpu_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_gpu', 'GPU % schedutil', labels=['gpu'])
            g.add_metric(['val'], self._jetson.gpu['gpu']['status']['load'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting GPU usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_ram_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_ram', 'Memory usage', labels=['device', 'type'])
            g.add_metric(['ram', 'used'], self._jetson.memory['RAM']['used'])
            g.add_metric(['ram', 'total'], self._jetson.memory['RAM']['tot'])
            g.add_metric(['swap', 'used'], self._jetson.memory['SWAP']['used'])
            g.add_metric(['swap', 'total'], self._jetson.memory['SWAP']['tot'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting RAM usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_disk_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_disk', 'Disk space usage', labels=['disk'])
            g.add_metric(['used'], self._jetson.disk['used'])
            g.add_metric(['total'], self._jetson.disk['total'])
            g.add_metric(['available'], self._jetson.disk['available'])
            g.add_metric(['available_no_root'], self._jetson.disk['available_no_root'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting disk usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_fan_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_fan', 'Fan usage', labels=['fan'])
            g.add_metric(['speed'], self._jetson.fan['pwmfan']['speed'][0])
            yield g
        except JtopException as e:
            print("Jtop Error collecting fan usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_sensor_temperatures(self):
        try:
            g = GaugeMetricFamily('jetson_temperatures', 'Sensor temperatures', labels=['device'])
            for item in self._jetson.temperature:
                if self._jetson.temperature[item]['online']:
                    g.add_metric([item], self._jetson.temperature[item]['temp'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting sensor temperatures: " + str(e))

    def collect_power_usage(self):
        try:
            g = GaugeMetricFamily('jetson_usage_power', 'Power usage', labels=['power'])
            for item in self._jetson.power['rail']:
                if self._jetson.power['rail'][item]['online']:
                    g.add_metric([item], self._jetson.power['rail'][item]['power'])
            g.add_metric(['total'], self._jetson.power['tot']['power'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting power usage: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_voltages(self):
        try:
            g = GaugeMetricFamily('jetson_voltages', 'Voltages', labels=['volts','power'])
            for item in self._jetson.power['rail']:
                if self._jetson.power['rail'][item]['online']:
                    g.add_metric([item], self._jetson.power['rail'][item]['volt'])
            yield g
        except JtopException as e:
            print("Jtop Error collecting voltages: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))

    def collect_network_interfaces(self):
        try:
            i = InfoMetricFamily('jetson_network', 'Network info', labels=['interface_name'])
            for netName, ip in self._jetson.local_interfaces['interfaces'].items():
                i.add_metric([netName], {'ip_address': ip})
            yield i
        except JtopException as e:
            print("Jtop Error collecting network interfaces: " + str(e))
        except Exception as e:
            print("Error collecting board info: " + str(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help='Metrics collector port number')
    args = parser.parse_args()

    start_http_server(args.port)
    REGISTRY.register(JetsonNanoCollector())
    
    while(True):
        time.sleep(60)