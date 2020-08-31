from oftester.constants import GROUP_ID


def group_output_in_two_ports(dpid, first_out_port, second_out_port):
    """
    Group that sends packet to ports.

    :param dpid: Switch DPID
    :param first_out_port: first out port
    :param second_out_port: second out port
    :return: (dict)
    """
    return {
        'dpid': dpid,
        'type': 'ALL',
        'group_id': GROUP_ID,
        'buckets': [
            {
                'actions': [
                    {
                        'type': 'OUTPUT',
                        'port': first_out_port
                    }
                ]
            }, {
                'actions': [
                    {
                        'type': 'OUTPUT',
                        'port': second_out_port
                    }
                ]
            }
        ]
    }


def group_rtl(dpid, first_out_port, second_out_port, mac='aa:bb:cc:dd:ee:ff', udp_port=5000):
    """
    Group that sends packet to ports.

    :param dpid: Switch DPID
    :param first_out_port: (int) first out port
    :param second_out_port: (int) second out port
    :param mac: (string) mac to use in eth_dst packet header
    :param udp_port: (int) udp destination port
    :return: (dict)
    """
    return {
        'dpid': dpid,
        'type': 'ALL',
        'group_id': GROUP_ID,
        'buckets': [
            {
                'actions': [
                    {
                        'type': 'SET_FIELD',
                        'field': 'eth_dst',
                        'value': mac
                    }, {
                        'type': 'OUTPUT',
                        'port': first_out_port
                    }
                ]
            }, {
                'actions': [
                    {
                        'type': 'SET_FIELD',
                        'field': 'udp_dst',
                        'value': udp_port
                    }, {
                        'type': 'OUTPUT',
                        'port': second_out_port
                    }
                ]
            }
        ]
    }
