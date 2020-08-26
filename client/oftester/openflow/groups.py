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
