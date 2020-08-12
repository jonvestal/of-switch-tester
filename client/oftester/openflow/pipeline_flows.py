from oftester.constants import *

INPUT_TABLE_ID = 0
PRE_INGRESS_TABLE_ID = 1
INGRESS_TABLE_ID = 2
POST_INGRESS_TABLE_ID = 3
EGRESS_TABLE_ID = 4
TRANSIT_TABLE_ID = 5


def flow_ingress_vlan(dpid, in_port, out_port, outer_vid, inner_vid=None, transit_vid=48,
                      priority=2000):
    """
    Creates flows that will pop 8100 VLAN and replace 8100 VLAN or flow that will replace 8100 VLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param outer_vid: (int) outer vlan id
    :param inner_vid: (int) inner vlan id
    :param transit_vid: (int) transit vlan id
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    flows = [
        {
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port
            },
            'actions': [{'type': 'GOTO_TABLE', 'table_id': PRE_INGRESS_TABLE_ID}]
        }
    ]

    flows.insert(0, {
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': PRE_INGRESS_TABLE_ID,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'vlan_vid': outer_vid
        },
        'actions': [
            {
                'type': 'POP_VLAN'
            },
            {
                'type': 'WRITE_METADATA',
                'metadata': 1,
                'metadata_mask': 1
            },
            {
                'type': 'GOTO_TABLE',
                'table_id': INGRESS_TABLE_ID
            }]
    })

    match = {
        'metadata': 1,
        'in_port': in_port,
    }

    actions = [{'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': transit_vid},
               {'type': 'OUTPUT', 'port': out_port}]
    if inner_vid:
        match['vlan_vid'] = inner_vid
    else:
        actions.insert(0, {'type': 'PUSH_VLAN', 'ethertype': 33024})

    flows.insert(0, {
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VLAN,
        'table_id': INGRESS_TABLE_ID,
        'priority': priority,
        'match': match,
        'actions': actions
    })

    return flows


def flow_egress_vlan(dpid, in_port, out_port, outer_vid=46, inner_vid=None, transit_vid=48,
                     priority=2000):
    """
    Creates a flow that will replace 8100 VLAN and push new 8100 VLAN if outer_vid is not None.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param inner_vid: (int) inner vlan id
    :param outer_vid: (int) outer vlan id
    :param transit_vid: (int) transit vlan id
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    flows = [
        {
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port
            },
            'actions': [{'type': 'GOTO_TABLE', 'table_id': EGRESS_TABLE_ID}]
        }
    ]
    actions = []

    if inner_vid:
        actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': inner_vid})
        actions.append({'type': 'PUSH_VLAN', 'ethertype': 33024})

    actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': outer_vid})
    actions.append({'type': 'OUTPUT', 'port': out_port})

    flows.insert(0, {
        'dpid': dpid,
        'cookie': COOKIE_EGRESS_VLAN,
        'table_id': EGRESS_TABLE_ID,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'vlan_vid': transit_vid
        },
        'actions': actions
    })
    return flows


def flow_ingress_vxlan(dpid, in_port, out_port, outer_vid=46, inner_vid=None,
                       priority=2000, src_ip='192.168.0.1', dst_ip='192.168.0.2',
                       src_mac='11:22:33:44:55:66', dst_mac='aa:bb:cc:dd:ee:ff',
                       udp_port=5000, vni=4242):
    """
    Creates flows that will pop two 8100 VLAN tags and push VxLAN.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param outer_vid: (int) outer vlan id
    :param inner_vid: (int) inner vlan id
    :param priority: (int) priority of the flow
    :param src_ip: (string) ip address to use in src_ip VxLAN header
    :param dst_ip: (string) ip address to use in dst_ip VxLAN header
    :param src_mac: (string) mac to use in eth_src VxLAN header
    :param dst_mac: (string) mac to use in eth_dst VxLAN header
    :param udp_port: (int) udp_port for the VxLAN header
    :param vni: (int) VxLAN ID
    :return: (dict)
    """

    flows = [
        {
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VXLAN,
            'table_id': PRE_INGRESS_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port,
                'vlan_vid': outer_vid
            },
            'actions': [
                {
                    'type': 'POP_VLAN'
                },
                {
                    'type': 'WRITE_METADATA',
                    'metadata': 1,
                    'metadata_mask': 1
                },
                {
                    'type': 'GOTO_TABLE',
                    'table_id': INGRESS_TABLE_ID
                }]
        },
        {
            'dpid': dpid,
            'cookie': COOKIE_INGRESS_VXLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port
            },
            'actions': [{'type': 'GOTO_TABLE', 'table_id': PRE_INGRESS_TABLE_ID}]
        }
    ]

    match = {
        'metadata': 1,
        'in_port': in_port,
    }

    actions = [
        {
            'type': 'NOVI_PUSH_VXLAN',
            'eth_src': src_mac,
            'eth_dst': dst_mac,
            'ipv4_src': src_ip,
            'ipv4_dst': dst_ip,
            'udp_src': udp_port,
            'vni': vni
        },
        {
            'type': 'OUTPUT',
            'port': out_port
        }
    ]

    if inner_vid:
        match['vlan_vid'] = inner_vid
        actions.insert(0, {'type': 'POP_VLAN'})

    flows.insert(0, {
        'dpid': dpid,
        'cookie': COOKIE_INGRESS_VXLAN,
        'table_id': INGRESS_TABLE_ID,
        'priority': priority,
        'match': match,
        'actions': actions
    })

    return flows


def flow_egress_vxlan(dpid, in_port, out_port, outer_vid=46, inner_vid=None, vni=4242,
                      priority=2000):
    """
    Creates a flow that will pop VxLAN and push two 8100 VLAN tags.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param outer_vid: (int) outer vlan id
    :param inner_vid: (int) inner vlan id
    :param vni: (int) VxLAN ID
    :param priority: (int) priority of the flow
    :return: (dict)
    """

    flows = [
        {
            'dpid': dpid,
            'cookie': COOKIE_EGRESS_VXLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port
            },
            'actions': [{'type': 'GOTO_TABLE', 'table_id': EGRESS_TABLE_ID}]
        }
    ]

    actions = [{'type': 'NOVI_POP_VXLAN'}]

    if inner_vid:
        actions.append({'type': 'PUSH_VLAN', 'ethertype': 33024})
        actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': inner_vid})

    actions.append({'type': 'PUSH_VLAN', 'ethertype': 33024})
    actions.append({'type': 'SET_FIELD', 'field': 'vlan_vid', 'value': outer_vid})

    actions.append({'type': 'OUTPUT', 'port': out_port})

    flows.insert(0, {
        'dpid': dpid,
        'cookie': COOKIE_EGRESS_VXLAN,
        'table_id': EGRESS_TABLE_ID,
        'priority': priority,
        'match': {
            'in_port': in_port,
            'eth_type': 2048,
            'ip_proto': 17,
            'udp_dst': 4789,
            'tunnel_id': vni
        },
        'actions': actions
    })
    return flows


def flow_transit_vlan(dpid, in_port, out_port, transit_vid=48, priority=2000):
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

    return [
        {
            'dpid': dpid,
            'cookie': COOKIE_TRANSIT_VLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port,
            },
            'actions': [{
                'type': 'GOTO_TABLE',
                'table_id': EGRESS_TABLE_ID
            }]
        },
        {
            'dpid': dpid,
            'cookie': COOKIE_TRANSIT_VLAN,
            'table_id': EGRESS_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port,
            },
            'actions': [{
                'type': 'GOTO_TABLE',
                'table_id': TRANSIT_TABLE_ID
            }]
        },
        {
            'dpid': dpid,
            'cookie': COOKIE_TRANSIT_VLAN,
            'table_id': TRANSIT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port,
                'vlan_vid': transit_vid
            },
            'actions': [{'type': 'OUTPUT', 'port': out_port}]
        }]


def flow_transit_vxlan(dpid, in_port, out_port, priority=2000, vni=4242):
    """
    Creates a flow that will match VxLAN id and throw packet to out port.

    :param dpid: Switch DPID
    :param in_port: (int) port to match for incoming packets
    :param out_port: (out) port to send packet out
    :param priority: (int) priority of the flow
    :param vni: (int) VxLAN ID
    :return: (dict)
    """

    return [
        {
            'dpid': dpid,
            'cookie': COOKIE_TRANSIT_VXLAN,
            'table_id': INPUT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port
            },
            'actions': [{
                'type': 'GOTO_TABLE',
                'table_id': TRANSIT_TABLE_ID
            }]
        },
        {
            'dpid': dpid,
            'cookie': COOKIE_TRANSIT_VXLAN,
            'table_id': TRANSIT_TABLE_ID,
            'priority': priority,
            'match': {
                'in_port': in_port,
                'eth_type': 2048,
                'ip_proto': 17,
                'udp_dst': 4789,
                'tunnel_id': vni
            },
            'actions': [{'type': 'OUTPUT', 'port': out_port}]
        }]
