class Renderer():

    def __init__(self, name, control_url, with_metadata=False):
        self._name = name
        self._control_url = control_url
        self._with_metadata = with_metadata

    def get_name(self):
        return self._name

    def include_metadata(self):
        return self._with_metadata

    def get_url(self):
        return self._control_url
