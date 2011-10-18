import socket


class SimpleConfig(object):
    "Simple configuration file parser"

    def __init__(self, filename):
        self.filename = filename
        self.load()
    
    def load(self):
        items = {}
        with open(self.filename) as fh:
            for line in fh:
                # Clean up line, remove comments
                line = line.strip()
                if "#" in line:
                    line = line[:line.index("#")].strip()
                # Get the values
                if line:
                    try:
                        variable, value = line.split("=", 1)
                    except ValueError:
                        raise ValueError("Bad config line (no = and not a comment): %s" % line)
                    items.setdefault(variable.strip().lower(), set()).add(value.strip())
        # Save to ourselves
        self.items = items
    
    def __getitem__(self, item):
        values = self.items[item]
        if len(values) > 1:
            raise ValueError("More than one value specified for %s" % item)
        return list(values)[0]
    
    def get(self, item, default=None):
        values = self.items.get(item, set())
        if len(values) == 0:
            return default
        if len(values) > 1:
            raise ValueError("More than one value specified for %s" % item)
        return list(values)[0]
    
    def get_int(self, item, default):
        return int(self.get(item, default))
    
    def get_all(self, item):
        return self.items.get(item, set())
    
    def get_all_addresses(self, item, default=None):
        addresses = set()
        for value in self.get_all(item):
            try:
                address, port = value.rsplit(":", 1)
                family = socket.AF_INET
            except ValueError:
                raise ValueError("Invalid address (no port found): %s" % value)
            if address[0] == "[":
                address = address.strip("[]")
                family = socket.AF_INET6
            if address == "*":
                address = "::"
                family = socket.AF_INET6
            addresses.add(((address, int(port)), family))
        if not addresses:
            addresses = default or set()
        return addresses
