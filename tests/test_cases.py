import openflow.noviflow_flows as novi
import base64
import socket
import pytest

src_ip = "192.168.0.1"
dst_ip = "192.168.0.2"
src_mac = "112233445566"
dst_mac = "aabbccddeeff"
udp_port = 4242
vin = 1


def test_make_base64():
    assert base64.b64decode(novi.make_base64("ff000002ff00")).hex() == "ff000002ff00"


def test_make_experimenter():
    data = novi.make_base64('ffffffffff')
    action = novi.make_experimenter_action(data)
    assert action['type'] == 'EXPERIMENTER'
    assert action['experimenter'] == 4278190082
    assert action['data'] == data
    assert action['data_type'] == 'base64'


def test_action_payload_vxlan_push():
    action = novi.action_payload_vxlan_push(src_ip, dst_ip, src_mac, dst_mac, udp_port, vin)
    s = base64.b64decode(action)
    assert s[:6].hex() == 'ff0000020001'
    assert s[6:12].hex() == src_mac
    assert s[12:18].hex() == dst_mac
    assert socket.inet_ntoa(s[18:22]) == src_ip
    assert socket.inet_ntoa(s[22:26]) == dst_ip
    assert int.from_bytes(s[26:30], 'big') == udp_port
    assert int.from_bytes(s[30:], 'big') == vin


@pytest.mark.parametrize("src_ip, dst_ip, src_mac, dst_mac, udp_port, vin", [
    (src_ip, dst_ip, src_mac, dst_mac, 100000, vin),
    (src_ip, dst_ip, src_mac, dst_mac, udp_port, -1)
])
def test_exception_on_values_vxlan(src_ip, dst_ip, src_mac, dst_mac, udp_port, vin):
    with pytest.raises(ValueError):
        novi.action_payload_vxlan_push(src_ip, dst_ip, src_mac, dst_mac, udp_port, vin)


def test_action_payload_vxlan_push_multi():
    action = novi.action_payload_vxlan_push(flags=0x00)
    s = base64.b64decode(action)
    assert s.hex() == 'ff0000020000000000'


def test_action_payload_vxlan_pop():
    action = novi.action_payload_vxlan_pop()
    s = base64.b64decode(action)
    assert s.hex() == 'ff00000300000000'






