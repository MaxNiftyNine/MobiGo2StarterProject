import struct
import unittest

from device import BLOCK_SIZE, MobiGoFS
from install_mba import slot_path


def response(status=0):
    data = bytearray(BLOCK_SIZE)
    struct.pack_into("<h", data, 0, status)
    return bytes(data)


class ScriptedTransport:
    def __init__(self, reads=()):
        self.reads = list(reads)
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size):
        data = self.reads.pop(0)
        if len(data) != size:
            raise AssertionError((len(data), size))
        return data


class FilesystemProtocolTests(unittest.TestCase):
    def test_zero_byte_dmode_write_finishes_rpc(self):
        transport = ScriptedTransport(
            [
                response(ord("A")),
                response(7),
                response(),
                response(),
                response(),
                response(),
                response(),
                response(),
            ]
        )
        MobiGoFS(transport).write_file("/ETC/DMODE", b"")
        commands = [struct.unpack_from("<I", item)[0] for item in transport.writes]
        self.assertEqual(commands, [0x16, 2, 0x0C, 0x0D, 4, 0x0C, 0x0D, 5])
        open_request = transport.writes[1]
        self.assertEqual(open_request[4:16], b"A:\\ETC\\DMODE")
        self.assertEqual(struct.unpack_from("<H", open_request, 46)[0], 2)
        write_request = transport.writes[4]
        self.assertEqual(struct.unpack_from("<I", write_request, 8)[0], 0)

    def test_storage_response(self):
        reply = bytearray(BLOCK_SIZE)
        struct.pack_into("<h", reply, 0, 0)
        struct.pack_into("<II", reply, 4, 64 * 1024 * 1024, 7 * 1024 * 1024)
        self.assertEqual(
            MobiGoFS(ScriptedTransport([bytes(reply)])).info(),
            (64 * 1024 * 1024, 7 * 1024 * 1024),
        )

    def test_directory_record(self):
        reply = bytearray(BLOCK_SIZE)
        struct.pack_into("<h", reply, 0, 4)
        reply[4:16] = b"135804SY.MBA"
        struct.pack_into("<H", reply, 18, 1)
        struct.pack_into("<I", reply, 24, 1234)
        struct.pack_into("<h", reply, 28, -1)
        transport = ScriptedTransport([response(ord("A")), bytes(reply)])
        entries = list(MobiGoFS(transport).listdir("/BUNDLE/SY"))
        self.assertEqual([(e.name, e.size, e.kind) for e in entries], [
            ("135804SY.MBA", 1234, 1)
        ])

    def test_delete_packet(self):
        transport = ScriptedTransport([response(ord("A")), response()])
        MobiGoFS(transport).delete("/MobiGo2Starter.MBA")
        request = transport.writes[1]
        self.assertEqual(struct.unpack_from("<I", request, 0)[0], 8)
        self.assertEqual(
            request[4:26].rstrip(b"\0"), b"A:\\MobiGo2Starter.MBA"
        )

    def test_system_slot_accepts_us_filename(self):
        class FakeFS:
            def listdir(self, path):
                self.path = path
                return [
                    type("Entry", (), {
                        "name": "135800SY.MBA", "kind": 1
                    })()
                ]

        fs = FakeFS()
        self.assertEqual(slot_path(fs, "system"), "/BUNDLE/SY/135800SY.MBA")
        self.assertEqual(fs.path, "/BUNDLE/SY")


if __name__ == "__main__":
    unittest.main()
