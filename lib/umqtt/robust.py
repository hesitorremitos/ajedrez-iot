from .simple import MQTTClient


class MQTTClient(MQTTClient):
    DELAY = 2
    DEBUG = False

    def delay(self, i):
        import time

        time.sleep(self.DELAY)

    def log(self, msg):
        if self.DEBUG:
            print(msg)

    def reconnect(self):
        i = 0
        while True:
            try:
                return self.connect()
            except OSError as e:
                self.log("Reconnect failed: %r" % e)
                i += 1
                self.delay(i)

    def publish(self, topic, msg, retain=False, qos=0):
        while True:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError:
                self.reconnect()

    def subscribe(self, topic, qos=0):
        while True:
            try:
                return super().subscribe(topic, qos)
            except OSError:
                self.reconnect()

    def check_msg(self):
        while True:
            try:
                return super().check_msg()
            except OSError:
                self.reconnect()
