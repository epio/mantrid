from eventlet.greenpool import GreenPool
from eventlet.event import Event


class GreenBody(GreenPool):
    """
    Special subclass of GreenPool which has a wait() method,
    that will return when any greenthread inside the pool exits.
    """

    def __init__(self, *args, **kwargs):
        super(GreenBody, self).__init__(*args, **kwargs)
        self.one_exited = Event()

    def wait(self):
        return self.one_exited.wait()
    
    def _spawn_done(self, coro):
        super(GreenBody, self)._spawn_done(coro)
        self.one_exited.send(coro.wait())
