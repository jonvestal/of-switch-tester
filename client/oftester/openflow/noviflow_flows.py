# Deprecated

import codecs
import socket

NOVIFLOW_EXPERIMENTER = 0xff000002
NOVIFLOW_CUSTOMER = "ff"
NOVIFLOW_RESERVE = "00"
NOVIFLOW_HEADER = int(NOVIFLOW_EXPERIMENTER)


def make_base64(data):
    """
    Takes a string of hex values and returns a base64 encoded string.

    :param data: string of Hex
    :return: base64 encoded string
    """
    return codecs.encode(
        codecs.decode(data, 'hex'), 'base64').decode('utf-8').replace('\n', '')


def make_experimenter_action(data, data_type='base64'):
    """
    Creates an OpenFlow experimenter action.

    :param data: Base64 encoded string or ASCII
    :param data_type: Type of encoding used for data
    :return: Dict used as an action in Ryu flowentry/add
    """

    return {
        'type': 'EXPERIMENTER',
        'experimenter': NOVIFLOW_HEADER,
        'data': data,
        'data_type': data_type
    }


def action_payload_vxlan_push(src_ip=None, dst_ip=None, src_mac=None,
                              dst_mac=None, udp_port=0, vni=0, flags=0x01):
    """
    Returns an RYU action that will create a vxlan_push action for Noviflow.
        novi_action_type: 0x0002
        tunnel_type: 0x00
        flags: 0x00
        eth_src: uint8[6]
        eth_dst: uint8[6]
        ipv4_src: uint32
        ipv4_dst: uint32
        udp_src: uint16
        vni: uint32

    :param flags: hex value with 0x00 meaning tunnel data not present
    :param src_ip: source ip address in dotted quad notation as a string
    :param dst_ip: destination ip address in dotted quad notation as a string
    :param src_mac: source mac address as a string of hex (no : or -
    with leading 0's)
    :param dst_mac: destination mac address as a string of hex (no : or -
    with leading 0's)
    :param udp_port: integer with maximum value of 65536
    :param vni: integer with maximum value of 4294967295
    :return: String
    """
    action_type = '0002'
    tunnel_type = '00'

    if flags == 1:
        if udp_port < 0 or udp_port > 65536:
            raise ValueError("UDP port needs to be between 0 and 65536")

        if vni < 0 or vni > 4294967295:
            raise ValueError("VIN needs to be between 0 and 429467295")
        return make_base64("{}{}{}{}{}{}{}{}{}{}{}".format(
            NOVIFLOW_CUSTOMER, NOVIFLOW_RESERVE, action_type, tunnel_type,
            "01", src_mac, dst_mac, socket.inet_aton(src_ip).hex(),
            socket.inet_aton(dst_ip).hex(), "{:0{}x}".format(udp_port, 8),
            "{:0{}x}".format(vni, 16)))
    else:
        return make_base64("{}{}{}{}{}000000"
                           .format(NOVIFLOW_CUSTOMER, NOVIFLOW_RESERVE,
                                   action_type, tunnel_type, "00"))


def action_payload_vxlan_pop():
    """
    Return a RYU action that will create a vxlan_pop action for Noviflow

        novi_action_type: 0x0003
        tunnel_type: 0x00
        pad[3]

    :return: String
    """
    action_type = '0003'
    tunnel_type = '00'
    pad = '000000'

    return make_base64("{}{}{}{}{}".format(NOVIFLOW_CUSTOMER, NOVIFLOW_RESERVE,
                                           action_type, tunnel_type, pad))
