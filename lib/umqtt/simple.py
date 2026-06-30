import errno
import socket
import struct

try:
    import ussl as ssl
except ImportError:
    ssl = None


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=0,
        ssl=None,
    ):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False
        self.cb = None
        self.last_will = False

    def _encode(self, length):
        if length < 128:
            return bytes([length])
        out = bytearray()
        while length > 0:
            digit = length % 128
            length //= 128
            if length > 0:
                digit |= 0x80
            out.append(digit)
        return bytes(out)

    def _send_str(self, s):
        self.sock.write(struct.pack("!H", len(s)))
        self.sock.write(s)

    def _recv_len(self):
        n = 0
        sh = 0
        while True:
            b = self.sock.read(1)[0]
            n |= (b & 0x7F) << sh
            if not b & 0x80:
                return n
            sh += 7

    def set_callback(self, f):
        self.cb = f

    def set_last_will(self, topic, msg, retain=False, qos=0):
        if self.last_will:
            raise MQTTException("Last will already set")
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain
        self.last_will = True

    def connect(self, clean_session=True):
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port, 0, socket.SOCK_STREAM)[0][-1]
        self.sock.connect(addr)
        if self.ssl:
            self.sock = ssl.wrap_socket(self.sock, **self.ssl)
        msg = bytearray(b"\x04MQTT\x04")
        msg.append(0x02 if clean_session else 0x00)
        msg.extend(struct.pack("!H", self.keepalive))
        msg.extend(bytearray(self.client_id))
        if self.lw_topic:
            msg.append(0x04 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3)
            msg.extend(bytearray(self.lw_topic))
            msg.extend(struct.pack("!H", len(self.lw_msg)))
            msg.extend(bytearray(self.lw_msg))
        if self.user:
            msg.append(0x80)
            msg.extend(bytearray(self.user))
            if self.pswd:
                msg.append(0x40)
                msg.extend(bytearray(self.pswd))
        pkt = bytearray(b"\x10")
        pkt.extend(self._encode(len(msg)))
        pkt.extend(msg)
        self.sock.write(pkt)
        if self.sock.read(1)[0] != 0x20:
            raise MQTTException("Bad CONNACK")
        if self.sock.read(1)[0] != 0x00:
            raise MQTTException("CONNACK rejected")

    def disconnect(self):
        try:
            self.sock.write(b"\xe0\x00")
        except OSError:
            pass
        self.sock.close()

    def ping(self):
        self.sock.write(b"\xc0\x00")

    def publish(self, topic, msg, retain=False, qos=0):
        pkt = bytearray(b"\x30")
        pkt.append(qos << 1 | retain)
        rem_len = 2 + len(topic) + len(msg)
        if qos > 0:
            rem_len += 2
        pkt.extend(self._encode(rem_len))
        pkt.extend(struct.pack("!H", len(topic)))
        pkt.extend(topic)
        if qos > 0:
            pkt.extend(b"\x00\x01")
        pkt.extend(msg)
        self.sock.write(pkt)

    def subscribe(self, topic, qos=0):
        pkt = bytearray(b"\x82")
        rem_len = 2 + 2 + len(topic) + 1
        pkt.extend(self._encode(rem_len))
        pkt.extend(b"\x00\x01")
        pkt.extend(struct.pack("!H", len(topic)))
        pkt.extend(topic)
        pkt.append(qos)
        self.sock.write(pkt)
        if self.sock.read(1)[0] != 0x90:
            raise MQTTException("Bad SUBACK")

    def wait_msg(self):
        res = self.sock.read(1)
        if not res:
            return None
        if res == b"":
            self.sock.close()
            raise OSError(-1, "Connection closed")
        if ord(res) & 0xF0 != 0x30:
            return None
        sz = self._recv_len()
        topic_len = self.sock.read(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = self.sock.read(topic_len)
        sz -= topic_len + 2
        if ord(res) & 6:
            self.sock.read(2)
            sz -= 2
        msg = self.sock.read(sz)
        self.cb(topic, msg)
        return msg

    def check_msg(self):
        self.sock.setblocking(False)
        try:
            return self.wait_msg()
        except OSError as e:
            if e.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return None
            raise
