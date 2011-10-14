try:
    import eventlet
    httplib2 = eventlet.import_patched("httplib2")
except ImportError:
    import httplib2
import json


class MantridClient(object):
    """
    Class encapsulating Mantrid client operations.
    """

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _request(self, path, method, body=None):
        "Base request function"
        h = httplib2.Http()
        resp, content = h.request(
            self.base_url + path,
            method,
            body = json.dumps(body),
        )
        if resp['status'] == "200":
            return json.loads(content)
        else:
            raise IOError(
                "Got %s reponse from server (%s)" % (
                    resp['status'],
                    content,
                )
            )
    
    def get_all(self):
        "Returns all endpoints"
        return self._request("/hostname/", "GET")
    
    def set_all(self, data):
        "Sets all endpoints"
        return self._request("/hostname/", "PUT", data)
    
    def set(self, hostname, entry):
        "Sets endpoint for a single hostname"
        return self._request("/hostname/%s/" % hostname, "PUT", entry)
    
    def delete(self, hostname):
        "Deletes a single hostname"
        return self._request("/hostname/%s/" % hostname, "DELETE")

    def stats(self, hostname=None):
        if hostname:
            return self._request("/stats/%s/" % hostname, "GET")
        else:
            return self._request("/stats/", "GET")
