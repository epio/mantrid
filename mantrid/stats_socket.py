class StatsSocket(object):
    """
    Wrapper around a socket that measures how many bytes
    have been sent and received.
    """

    def __init__(self, sock):
        self.sock = sock
        self.bytes_sent = 0
        self.bytes_received = 0

    def __getattr__(self, attr):
        return getattr(self.sock, attr)
    
    def sendall(self, data):
        self.bytes_sent += len(data)
        self.sock.sendall(data)
    
    def send(self, data):
        sent = self.sock.send(data)
        self.bytes_sent += sent
        return sent
    
    def recv(self, length):
        recvd = self.sock.recv(length)
        self.bytes_received += len(recvd)
        return recvd

    def makefile(self, *args, **kwargs):
        fh = self.sock.makefile(*args, **kwargs)
        fh._sock = self
        return fh
