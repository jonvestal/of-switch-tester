import copy

from constants import *


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


def metadata_milti_table_flows(dpid, in_port, out_port, priority=2000):
    return [
        {
            'dpid': dpid,
            'cookie': COOKIE_METADATA,
            'table_id': 0,
            'priority': priority,
            'match': {'in_port': in_port},
            "actions": [
                {
                    "type": "WRITE_METADATA",
                    "metadata": 1,
                    "metadata_mask": 1
                },
                {
                    'type': "GOTO_TABLE",
                    'table_id': 1
                }
            ]
        },
        {
            'dpid': dpid,
            'cookie': COOKIE_METADATA_OUT,
            'table_id': 1,
            'priority': priority,
            "actions": [
                {'type': 'OUTPUT', 'port': out_port}
            ]
        },
    ]


def pass_through_flow(dpid, in_port, out_port, priority=1000):
    return {
            'dpid': dpid,
            'cookie': COOKIE_PASS_THROUGH,
            'table_id': 0,
            'priority': priority,
            'match': {'in_port': in_port},
            "actions": [
                {'type': 'OUTPUT', 'port': out_port}
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


def flow_vlan_push_pop(dpid, in_port, out_port, action, vid=None, table_id=0, priority=2000):
    """
    Creates a flow that will either push an 8100 VLAN or pop and 8100 VLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param action: (string) PUSH/POP if PUSH will add header, POP removes header
    :param vid: (int) vlan id if not set will not push a vlan
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

        if vid is not None:
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


def flow_vxlan_push(dpid, in_port, out_port, table_id=0, priority=2000,
                    src_ip='192.168.0.1', dst_ip='192.168.0.2',
                    src_mac='11:22:33:44:55:66', dst_mac='aa:bb:cc:dd:ee:ff',
                    udp_port=5000, vni=4242, flags=1):
    """
    Create a VXLAN PUSH flow.

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
    actions = []
    if flags:
        actions.append({'type': 'NOVI_PUSH_VXLAN', 'eth_src': src_mac, 'eth_dst': dst_mac,
                        'ipv4_src': src_ip, 'ipv4_dst': dst_ip, 'udp_src': udp_port, 'vni': vni})
    else:
        actions.append({'type': 'NOVI_PUSH_VXLAN'})
        actions.append({'type': 'SET_FIELD', 'field': 'eth_src', 'value': src_mac})
        actions.append({'type': 'SET_FIELD', 'field': 'eth_dst', 'value': dst_mac})
        actions.append({'type': 'SET_FIELD', 'field': 'ipv4_src', 'value': src_ip})
        actions.append({'type': 'SET_FIELD', 'field': 'ipv4_dst', 'value': dst_ip})
        actions.append({'type': 'SET_FIELD', 'field': 'udp_src', 'value': udp_port})
        actions.append({'type': 'SET_FIELD', 'field': 'tunnel_id', 'value': vni})
    actions.append({
        'type': 'OUTPUT',
        'port': out_port
    })
    return {
        'dpid': dpid,
        'cookie': COOKIE_VXLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }


def flow_vxlan_pop(dpid, in_port, out_port, table_id=0, priority=2000):
    """
    Create a VXLAN POP flow.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (int) port to send packet out
    :param table_id: (int) table to put flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    return {
        'dpid': dpid,
        'cookie': COOKIE_VXLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': [
            {'type': 'NOVI_POP_VXLAN'},
            {'type': 'OUTPUT', 'port': out_port}
        ]
    }


def flow_swap_fields(dpid, in_port, out_port, table_id=0, priority=2000, src='eth_src', dst='eth_dst',
                     src_offset=0, dst_offset=0, n_bits=48):
    """
    Create a swap fields flow.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (int) port to send packet out
    :param table_id: (int) table to put flow into
    :param priority: (int) priority of the flow
    :param src: (string) source field name, including novi experementer oxm's
    :param dst: (string) destination field name, including novi experementer oxm's
    :param src_offset: (int) source field offset
    :param dst_offset: (int) destination field offset
    :param n_bits: (int) bits to swap
    :return: (dict)
    """

    return {
        'dpid': dpid,
        'cookie': COOKIE_SWAP_FIELDS,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': [
            {
                'type': 'NOVI_SWAP_FIELD',
                'n_bits': n_bits,
                'src_offset': src_offset,
                'dst_offset': dst_offset,
                'src': src,
                'dst': dst
            },
            {'type': 'OUTPUT', 'port': out_port}
        ]
    }


def flow_copy_fields(dpid, in_port, out_port, table_id=0, priority=2000, src='eth_src', dst='eth_dst',
                     src_offset=0, dst_offset=0, n_bits=48):
    """
    Create a copy fields flow.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (int) port to send packet out
    :param table_id: (int) table to put flow into
    :param priority: (int) priority of the flow
    :param src: (string) source field name, including novi experementer oxm's
    :param dst: (string) destination field name, including novi experementer oxm's
    :param src_offset: (int) source field offset
    :param dst_offset: (int) destination field offset
    :param n_bits: (int) bits to copy
    :return: (dict)
    """

    return {
        'dpid': dpid,
        'cookie': COOKIE_COPY_FIELDS,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': [
            {
                'type': 'NOVI_COPY_FIELD',
                'n_bits': n_bits,
                'src_offset': src_offset,
                'dst_offset': dst_offset,
                'src': src,
                'dst': dst
            },
            {'type': 'OUTPUT', 'port': out_port}
        ]
    }


def flow_set_fields(dpid, in_port, out_port, table_id=0, priority=2000, values=None):
    """
    Create a flow with set fields.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (int) port to send packet out
    :param table_id: (int) table to put flow into
    :param priority: (int) priority of the flow
    :param values: (dict) field/value pairs
    :return: (dict)
    """
    if not values:
        values = {}

    actions = []
    for field, value in values.items():
        actions.append({'type': 'SET_FIELD', 'field': field, 'value': value})
    actions.append({'type': 'OUTPUT', 'port': out_port})
    return {
        'dpid': dpid,
        'cookie': COOKIE_COPY_FIELDS,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': actions
    }


def flow_ingress_vlan(dpid, in_port, out_port, inner_vid=46, outer_vid=None, transit_vid=48,
                      table_id_0=0, table_id_1=1, priority=2000):
    """
    Creates flows that will pop 8100 VLAN and replace 8100 VLAN or flow that will replace 8100 VLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param inner_vid: (int) inner vlan id
    :param outer_vid: (int) outer vlan id
    :param transit_vid: (int) transit vlan id
    :param table_id_0: (int) table to pop outer vlan
    :param table_id_1: (int) table to pop inner vlan
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    flows = []
    table_id = table_id_0

    if outer_vid is not None:
        flows.append({
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VLAN,
            'table_id': table_id_0,
            'priority': priority,
            'match': {
                'in_port': in_port,
                'vlan_vid': outer_vid
            },
            'actions': [{'type': 'POP_VLAN'},
                        {'type': "GOTO_TABLE", 'table_id': table_id_1}]
        })
        table_id = table_id_1

    flows.append({
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'vlan_vid': inner_vid
        },
        'actions': [{'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': transit_vid},
                    {'type': 'OUTPUT', 'port': out_port}]
    })

    return flows


def flow_pop_vlan_and_push_new_vlans(dpid, in_port, out_port, inner_vid=46, outer_vid=None, transit_vid=48,
                                     table_id=0, priority=2000):
    """
    Creates a flow that will replace 8100 VLAN and push new 8100 VLAN and flow that will push two 8100 VLAN tags.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param inner_vid: (int) inner vlan id
    :param outer_vid: (int) outer vlan id
    :param transit_vid: (int) transit vlan id
    :param table_id: (int) table to put the flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    replace_actions = [{'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': inner_vid}]

    if outer_vid is not None:
        replace_actions.append({'type': 'PUSH_VLAN', 'ethertype': 33024})
        replace_actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': outer_vid})

    replace_actions.append({'type': 'OUTPUT', 'port': out_port})

    push_actions = copy.deepcopy(replace_actions)
    push_actions.insert(0, {'type': 'PUSH_VLAN', 'ethertype': 33024})

    return [{
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': table_id,
        'priority': priority + 1,
        'match': {
            'in_port': in_port,
            'vlan_vid': transit_vid
        },
        'actions': replace_actions
    }, {
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': push_actions
    }]


def flow_ingress_vxlan(dpid, in_port, out_port, inner_vid=46, outer_vid=None,
                       table_id_0=0, table_id_1=1, priority=2000,
                       src_ip='192.168.0.1', dst_ip='192.168.0.2',
                       src_mac='11:22:33:44:55:66', dst_mac='aa:bb:cc:dd:ee:ff',
                       udp_port=5000, vni=4242):
    """
    Creates flows that will pop two 8100 VLAN tags and push VxLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param inner_vid: (int) inner vlan id
    :param outer_vid: (int) outer vlan id
    :param table_id_0: (int) table to pop outer vlan
    :param table_id_1: (int) table to pop inner vlan
    :param priority: (int) priority of the flow
    :param src_ip: (string) ip address to use in src_ip VxLAN header
    :param dst_ip: (string) ip address to use in dst_ip VxLAN header
    :param src_mac: (string) mac to use in eth_src VxLAN header
    :param dst_mac: (string) mac to use in eth_dst VxLAN header
    :param udp_port: (int) udp_port for the VxLAN header
    :param vni: (int) VxLAN ID
    :return: (dict)
    """

    flows = []
    table_id = table_id_0

    if outer_vid is not None:
        flows.append({
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VXLAN,
            'table_id': table_id_0,
            'priority': priority,
            'match': {
                'in_port': in_port,
                'vlan_vid': outer_vid
            },
            'actions': [{'type': 'POP_VLAN'},
                        {'type': "GOTO_TABLE", 'table_id': table_id_1}]
        })
        table_id = table_id_1

    flows.append({
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VXLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'vlan_vid': inner_vid
        },
        'actions': [{'type': 'POP_VLAN'},
                    {'type': 'NOVI_PUSH_VXLAN', 'eth_src': src_mac, 'eth_dst': dst_mac,
                     'ipv4_src': src_ip, 'ipv4_dst': dst_ip, 'udp_src': udp_port, 'vni': vni},
                    {'type': 'OUTPUT', 'port': out_port}]
    })

    return flows


def flow_pop_vxlan_and_push_vlan(dpid, in_port, out_port, inner_vid=46, outer_vid=None, vni=4242,
                                 table_id=0, priority=2000):
    """
    Creates a flow that will pop VxLAN and push two 8100 VLAN tags and flow that will push two 8100 VLAN tags.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param inner_vid: (int) inner vlan id
    :param outer_vid: (int) outer vlan id
    :param vni: (int) VxLAN ID
    :param table_id: (int) table to put the flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    push_vlan_actions = [{'type': 'PUSH_VLAN', 'ethertype': 33024},
                         {'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': inner_vid}]

    if outer_vid is not None:
        push_vlan_actions.append({'type': 'PUSH_VLAN', 'ethertype': 33024})
        push_vlan_actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': outer_vid})

    push_vlan_actions.append({'type': 'OUTPUT', 'port': out_port})

    pop_vxlan_and_push_vlan_actions = copy.deepcopy(push_vlan_actions)
    pop_vxlan_and_push_vlan_actions.insert(0, {'type': 'NOVI_POP_VXLAN'})

    return [{
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': table_id,
        'priority': priority + 1,
        'match': {
            'in_port': in_port,
            'tunnel_id': vni
        },
        'actions': pop_vxlan_and_push_vlan_actions
    }, {
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VXLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {'in_port': in_port},
        'actions': push_vlan_actions
    }]


def flow_transit_vlan(dpid, in_port, out_port, transit_vid=48, table_id=0, priority=2000):
    """
    Creates a flow that will match 8100 VLAN and throw packet to out port.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param transit_vid: (int) transit vlan id
    :param table_id: (int) table to put the flow into
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    return {
        'dpid': dpid,
        'cookie': COOKIE_TRANSIT_VLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'vlan_vid': transit_vid
        },
        'actions': [{'type': 'OUTPUT', 'port': out_port}]
    }


def flow_transit_vxlan(dpid, in_port, out_port,  table_id=0, priority=2000, vni=4242):
    """
    Creates a flow that will match VxLAN id and throw packet to out port.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param table_id: (int) table to put the flow into
    :param priority: (int) priority of the flow
    :param vni: (int) VxLAN ID
    :return: (dict)
    """

    return {
        'dpid': dpid,
        'cookie': COOKIE_TRANSIT_VXLAN,
        'table_id': table_id,
        'priority': priority,
        'match': {
            'in_port': in_port,
            "eth_type": 2048,
            "ip_proto": 17,
            "udp_dst": 4789,
            'tunnel_id': vni
        },
        'actions': [{'type': 'OUTPUT', 'port': out_port}]
    }
