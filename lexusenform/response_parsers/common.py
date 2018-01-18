from xml.etree import ElementTree as et


class ResponseParser:
    """Base response parser"""
    def __init__(self, text, namespace = None):
        self.response_text = text
        self.root = et.fromstring(text)
        self.namespace = namespace

    def get_object(self):
        """Implement in subclass"""
        raise NotImplementedError()


class DummyParser(ResponseParser):
    """Return the XML as a string"""
    def get_object(self):
        return et.tostring(self.root)