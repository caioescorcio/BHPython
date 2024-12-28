from ctypes import *
import socket
import struct

class IP(Structure):
    _fields_ = [
        ("version",         c_ubyte,    4),  	# Unsigned char de 4 bits
        ("ihl",             c_ubyte,    4),  	# Unsigned char de 4 bits
        ("tos",             c_ubyte,    8),  	# char de 1 byte (8 bits)
        ("len",             c_ushort,  16),  	# Unsigned short de 2 bytes
        ("id",              c_ushort,  16),  	# Unsigned short de 2 bytes
        ("offset",          c_ushort,  16),  	# Unsigned short de 2 bytes
        ("ttl",             c_ubyte,    8),  	# char de 1 byte
        ("protocol_num",    c_ubyte,    8),  	# char de 1 byte
        ("sum",             c_ushort,  16),  	# Unsigned short de 2 bytes
        ("src",             c_uint32,  32),  	# Unsigned int de 4 bytes
        ("dst",             c_uint32,  32)  	# Unsigned int de 4 bytes
    ]
    
    def __new__ (cls, socket_buffer=None):
        return cls.from_buffer_copy(socket_buffer)
    
    def __init__ (self, socket_buffer=None):
        # Endereco de IP legivel por humanos
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))