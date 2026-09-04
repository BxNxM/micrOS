import socket
import threading
import unittest

from toolkit.lib.micrOSClient import micrOSClient


class MicrOSClientReceiveTests(unittest.TestCase):

    def test_receive_data_raises_when_peer_disconnects_before_prompt(self):
        client_socket, device_socket = socket.socketpair()
        self.addCleanup(client_socket.close)
        device_socket.close()

        client = micrOSClient("127.0.0.1", 9008)
        client.conn = client_socket
        client.prompt = "node $"

        with self.assertRaisesRegex(ConnectionError, "Device disconnected"):
            client._micrOSClient__receive_data(read_timeout=0.1)

    def test_send_cmd_retry_reconnects_after_device_disconnect(self):
        first_client, first_device = socket.socketpair()
        second_client, second_device = socket.socketpair()

        def serve_two_connections():
            with first_device:
                first_device.sendall(b"node $")
                first_device.recv(4096)

            with second_device:
                second_device.sendall(b"node $")
                second_device.recv(4096)
                second_device.sendall(b"3.4.2-0\nnode $")

        server_thread = threading.Thread(target=serve_two_connections, daemon=True)
        server_thread.start()

        client = micrOSClient("127.0.0.1", 9008)
        self.addCleanup(client.close)
        pending_connections = [first_client, second_client]

        def connect(_timeout):
            client.conn = pending_connections.pop(0)
            client.isconn = True

        client._micrOSClient__connect = connect

        response = client.send_cmd_retry("version", retry=2)

        self.assertEqual(["3.4.2-0"], response)
        server_thread.join(1)
        self.assertFalse(server_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
