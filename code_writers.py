class NamedObjectCodeWriter(object):
    """
    """
    object_inputs = []
    def __init__(self, class_name, name=None, **kwargs):
        self.name = name
        self.class_name = class_name
        self.kwargs = {}
        self.kwargs.update(kwargs)
        self.__class__.creation_counter += 1
        self.count = self.__class__.creation_counter
        self._object = None

    @property
    def bound_name(self):
        bind_str = "{}_{}".format(self.bound_label, str(self.count))
        return bind_str

    def _make_kwarg_str(self, key, value):
        if isinstance(value, str) and key not in self.object_inputs:
            value = '"' + value + '"'
        return "{key}={value}".format(key=key, value=value)

    @property
    def _call_str(self):
        kwarg_str = ", ".join([self._make_kwarg_str(key, value)
                               for key, value in self.kwargs.items()])
        call_str = "({kwargs})".format(kwargs=kwarg_str)
        return call_str

    @property
    def _name_str(self):
        if not self.name:
            return ""
        name_str = ".named('{name}')".format(name=self.name)
        return name_str

    @property
    def code(self):
        code_layout = "{bind_str} = paths.{class_name}{call_str}{name_str}"
        code_str = code_layout.format(bind_str=self.bound_name,
                                      class_name=self.class_name,
                                      call_str=self._call_str,
                                      name_str=self._name_str)
        return code_str

    def update(self, class_name, name, **kwargs):
        self.__init__(class_name, name, **kwargs)

    @classmethod
    def from_object(cls, obj):
        dct = obj.to_dict()
        try:
            name = dct.pop('name')
        except KeyError:
            name = None

        class_name = obj.__class__.__name__
        obj = cls(class_name, name, **dct)
        obj.object = obj
        return cls(class_name, name, **dct)

    @property
    def object(self):
        if self._object is not None:
            return self._object
        # TODO: add object creation here

    @object.setter
    def object(self, value):
        if self._object is None:
            self._object = value
        elif self._object != value:
            raise RuntimeError()
        # else we're setting object to what it already is; pass silently


class CVCodeWriter(NamedObjectCodeWriter):
    object_inputs = ['f']
    bound_label = "cv"
    creation_counter = 0
    def __init__(self, name, class_name, **kwargs):
        super(CVCodeWriter, self).__init__(class_name, name=name, **kwargs)
        self.kwargs['name'] = self.name
        self.name = None


class VolumeCodeWriter(NamedObjectCodeWriter):
    object_inputs = ['collectivevariable']
    bound_label = "volume"
    creation_counter = 0
    def __init__(self, class_name, is_state, name=None, **kwargs):
        super(VolumeCodeWriter, self).__init__(class_name, name, **kwargs)
        self.is_state = is_state

class StorageWriter(object):
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    @property
    def code(self):
        storage_str = "storage = paths.Storage('{filename}', mode='{mode}')"
        return storage_str.format(filename=self.filename, mode=self.mode)


class RandomizerWriter(object):
    pass
