import struct
from os.path import join, dirname, realpath
from socket import inet_aton


_unpack_V = lambda b: struct.unpack("<L", b)[0]
_unpack_N = lambda b: struct.unpack(">L", b)[0]
_unpack_C = lambda b: struct.unpack("B", b)[0]

with open(join(realpath(dirname(__file__)), '17monipdb.datx'), 'rb') as f:
    _db_binary = f.read()


class IPData(object):
    def __init__(self):
        self.binary = _db_binary
        self.offset = _unpack_N(self.binary[:4])
        self.index = self.binary[4:self.offset]

    def find(self, ip):
        index = self.index
        offset = self.offset
        binary = self.binary
        nip = inet_aton(ip)
        ipdot = ip.split('.')

        tmp_offset = (int(ipdot[0]) * 256 + int(ipdot[1])) * 4
        start = _unpack_V(index[tmp_offset:tmp_offset + 4])

        index_offset = index_length = -1
        max_comp_len = offset - 262144 - 4
        start = start * 9 + 262144

        while start < max_comp_len:
            if index[start:start + 4] >= nip:
                index_offset = _unpack_V(index[start + 4:start + 7] + chr(0).encode())
                index_length = _unpack_C(index[start + 8:start + 9])
                break
            start += 9

        if index_offset == 0:
            return None

        res_offset = offset + index_offset - 262144
        return binary[res_offset:res_offset + index_length].decode()


if __name__ == '__main__':
    print(IPData().find('112.192.238.247'))
