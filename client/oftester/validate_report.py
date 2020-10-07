#!/usr/bin/env python

import argparse
import json
from statistics import median, stdev


def main():
    args = get_args()

    with open(args.data) as f:
        data = json.loads(f.read())

    old_data = None
    if args.old_data:
        with open(args.old_data) as f:
            old_data = json.loads(f.read())

    allowed_change = {
        "min": args.min_change,
        "max": args.max_change,
        "median": args.median_change,
        "stdev": args.stdev_change
    }

    validate(allowed_change, data, old_data)


def validate(allowed_change, data, old_data=None):
    for packet_size in data:
        for d in data[packet_size]:
            values = get_data_values(d)
            old_d = None
            if old_data:
                for od in old_data[packet_size]:
                    if od['metric'] == d['metric']:
                        old_d = od
            old_values = get_data_values(old_d) if old_d else None
            process(packet_size, d['metric'], allowed_change,
                    values, old_values)


def get_data_values(data):
    d = data['dps']
    items = list(data['timestamps'].items())
    t = list(map(lambda x, y:
                 (int(x[0]), int(y[0]), y[1]), items[:-1], items[1:]))

    timestamps = list(d.keys())
    values = dict()
    for start, end, key in t:
        values[key] = list(map(d.get, list(
            filter(lambda x: start < int(x) < end, timestamps))))
    return values


def process(packet_size, metric, allowed_change, data, old_data=None):
    for scenario, values in data.items():
        old_values = None
        if old_data:
            for s, v in old_data.items():
                if s == scenario:
                    old_values = v

        data_result = calculate(values)
        old_data_result = None
        if old_values:
            old_data_result = calculate(old_values)

        print_result(scenario, packet_size, metric, allowed_change,
                     data_result, old_data_result)


def print_result(scenario, packet_size, metric, allowed_change,
                 data_result, old_data_result=None):
    print("Scenario: %s, Packet size: %s, Metric: %s:"
          % (scenario, packet_size, metric))

    change = dict()
    row_pattern = "%-10s| %-20s"
    titles = ['Function', 'New']
    rows = [list(data_result.keys()),
            get_list_strings_of_numbers(data_result.values())]
    if old_data_result:
        titles.append('Old')
        titles.append('Percent change')
        titles.append('Allowed percent change')
        rows.append(get_list_strings_of_numbers(old_data_result.values()))
        for key in data_result:
            change[key] = compute_percent_change(data_result[key],
                                                 old_data_result[key])
        rows.append(get_list_strings_of_numbers(change.values()))
        rows.append(get_list_strings_of_numbers(allowed_change.values()))
        row_pattern += "| %-20s| %-20s| %-20s"

    data = [tuple(titles)] + list(zip(*rows))
    for i, d in enumerate(data):
        line = row_pattern % d
        print(line)
        if i == 0:
            print('-' * len(line))

    if old_data_result:
        if change['min'] > allowed_change['min'] \
                and data_result['min'] < old_data_result['min']:
            print("ERROR: new min < old min")
        if change['max'] > allowed_change['max'] \
                and data_result['max'] < old_data_result['max']:
            print("WARN: new max < old max")
        if change['median'] > allowed_change['median'] \
                and data_result['median'] < old_data_result['median']:
            print("ERROR: new median < old median")
        if change['stdev'] > allowed_change['stdev'] \
                and data_result['stdev'] >= old_data_result['stdev']:
            print("WARN: new stdev >= old stdev")

    print()


def calculate(values):
    functions = [min, max, median, stdev]
    result = dict()
    for function in functions:
        result[function.__name__] = function(values)
    return result


def compute_percent_change(new, old):
    if old == 0:
        old = 0.00001
        if new == 0:
            new = 0.00001
    return (abs(new - old) / old) * 100


def get_list_strings_of_numbers(values):
    return [('%.5f' % x).rstrip('0').rstrip('.') for x in values]


def get_args():
    parser = argparse.ArgumentParser(description='Validate report data')

    parser.add_argument('data', action="store", metavar='data',
                        help="Json data file")
    parser.add_argument('--old', action="store", dest="old_data",
                        help="Old json data file")
    parser.add_argument('--min-change', action="store",
                        dest="min_change", default=1,
                        help="Permissible percentage change in min values")
    parser.add_argument('--max-change', action="store",
                        dest="max_change", default=1,
                        help="Permissible percentage change in max values")
    parser.add_argument('--median-change', action="store",
                        dest="median_change", default=1,
                        help="Permissible percentage change in median values")
    parser.add_argument('--stdev-change', action="store",
                        dest="stdev_change", default=10,
                        help="Permissible percentage change in stdev values")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
