from constants import *
import noviflow_flows as novi
import copy


def flow_loop_all_ports(dpid, table_id, priority=1):
    """
    Simple flow that matches everything and output to in_port

    :param dpid: Switch DPID
    :param table_id: (int) table to inject flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """
    return {
        'dpid': dpid,
        'cookie': COOKIE_LOOP,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': "OUTPUT",
                'port': OFPP_IN_PORT
            }
        ]
    }


def flow_goto_table(dpid, table_id, dst_table, priority):
    """
    Flow that matches everything and sends packet to another table

    :param dpid: Switch DPID
    :param table_id: (int) table to insert flow
    :param dst_table: (int) table that packet will be sent to
    :param priority: (int) priority of the flow
    :return: (dict)
    """
    return {
        'dpid': dpid,
        'cookie': COOKIE_GOTO_TABLE,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': "GOTO_TABLE",
                'table_id': dst_table
            }
        ]
    }


def flow_snake(dpid, start_port, end_port, table_id, priority=1000):
    """
    Sets up a snake through the switch.  Assumes that ports are connected in pairs of odd + 1, for example
    port 3 physical connected to port 4, 5 to 6, etc.  First port sends to last port and last port sends
    to first port.

    :param dpid: Switch DPID
    :param start_port: (int) first port of the snake
    :param end_port: (int) last port of the snake
    :param table_id: (int) table to put the snake into
    :param priority: (int) priority of the snake
    :return: (dict)
    """
    if end_port < start_port:
        raise ValueError

    flowmods = []

    flowmod = {
        'dpid': dpid,
        'cookie': COOKIE_SNAKE + table_id,
        'table_id': table_id,
        'priority': priority,
        'match': {},
        'actions': [
            {
                'type': 'OUTPUT',
                'port': -1
            }
        ]
    }

    x = start_port
    while x < end_port - 2:
        flowmod['match'] = {'in_port': x + 1}
        flowmod['actions'][0]['port'] = x + 2
        flowmods.append(copy.deepcopy(flowmod))
        x += 2
    flowmod['match'] = {'in_port': end_port}
    flowmod['actions'][0]['port'] = start_port
    flowmods.append(copy.deepcopy(flowmod))

    x = end_port
    while x > start_port + 2:
        flowmod['match'] = {'in_port': x - 1}
        flowmod['actions'][0]['port'] = x - 2
        flowmods.append(copy.deepcopy(flowmod))
        x -= 2
    flowmod['match'] = {'in_port': start_port}
    flowmod['actions'][0]['port'] = end_port
    flowmods.append(copy.deepcopy(flowmod))
    return flowmods


def flow_vlan_push_pop(dpid, in_port, out_port, action, vid=42, table_id=0, priority=2000):
    """
    Creates a flow that will either push an 8100 VLAN or pop and 8100 VLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param action: (string) PUSH/POP if PUSH will add header, POP removes header
    :param vid: (int) vlan id
    :param table_id: (int) table to put the flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """
    actions = [{
                'type': 'OUTPUT',
                'port': out_port
                }]
    if action == 'push':
        actions.insert(0, {'type': 'PUSH_VLAN', 'ethertype': 33024})
        actions.insert(1, {'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': vid})
    else:
        actions.insert(0, {'type': 'POP_VLAN'})

    return {
        'dpid': dpid,
        'cookie': COOKIE_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }


def flow_vxlan_push_pop(dpid, in_port, out_port, action, table_id=0, priority=2000,
                        src_ip='192.168.0.1', dst_ip='192.168.0.2',
                        src_mac='112233445566', dst_mac='aabbccddeeff',
                        udp_port=5000, vni=4242, flags=1):
    """
    Create a VXLAN PUSH or POP flow.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (int) port to send packet out
    :param action: (string) PUSH/POP  if PUSH will add header, POP removes header
    :param table_id: (int) table to put flow into
    :param priority: (int) priority of the flow
    :param src_ip: (string) ip address to use in src_ip VxLAN header
    :param dst_ip: (string) ip address to use in dst_ip VxLAN header
    :param src_mac: (string) mac to use in eth_src VxLAN header
    :param dst_mac: (string) mac to use in eth_dst VxLAN header
    :param udp_port: (int) udp_port for the VxLAN header
    :param vni: (int) VxLAN ID
    :param flags: (int) 0 = no header fields, 1 = add headers
    :return: (dict)
    """
    actions = [{
        'type': 'OUTPUT',
        'port': out_port
    }]
    if action == 'push':
        of_action = novi.make_experimenter_action(
            novi.action_payload_vxlan_push(src_ip, dst_ip, src_mac, dst_mac, udp_port, vni, flags))
    else:
        of_action = novi.make_experimenter_action(novi.action_payload_vxlan_pop())
    actions.insert(0, of_action)

    return {
        'dpid': dpid,
        'cookie': COOKIE_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }
