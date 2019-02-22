import sys
if sys.version_info > (3,):
    basestring = str

class StringWrapper(object):
    """Hack to allow special string to be printed correctly"""
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return self.string


class NamedObjectCodeWriter(object):
    """Model to capture input from GUI and create OPS code.

    To make things easier, we do everything as kwargs. There are also
    several special class attributes to be overridden in subclasses (this is
    an abstract class):

    * ``object_input``: names (keys) that correspond to named objects in the
      code. These will *not* be quoted as strings in the output.
    * ``bound_label``: objects will take ``bound_label`` as a prefix when
      we create code for these things. For example, the first CV created is
      called ``cv_1``: the ``bound_label`` is ``cv``.
    * ``creation_counter``: index of how many objects of this type we've
      made (starts at 0 so first object is 1). Used in code as seen in
      previous point.

    Parameters
    ----------
    class_name : str
        the name of the class to create; assumed to be ``paths.class_name``
    name : str or None
        the object's name; to be added with the ``.named(name)`` approach
    kwargs : dict
        everything else
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
        self.base = "paths"

    @property
    def bound_name(self):
        """name used for this object in code, e.g., ``cv_1``"""
        bind_str = "{}_{}".format(self.bound_label, str(self.count))
        return bind_str

    def _make_kwarg_str(self, key, value):
        if isinstance(value, basestring) and key not in self.object_inputs:
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
        """code to instantiate this object and bind it to a name"""
        code_layout = "{bind_str} = {base}.{class_name}{call_str}{name_str}"
        code_str = code_layout.format(bind_str=self.bound_name,
                                      base=self.base,
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
    object_inputs = ['f', 'engine']
    bound_label = "cv"
    creation_counter = 0
    def __init__(self, name, class_name, **kwargs):
        # special treatment of name, bc all OPS CVs must take names in
        # initialization
        super(CVCodeWriter, self).__init__(class_name, name=name, **kwargs)
        self.kwargs['name'] = self.name
        self.name = None
        self.base = "ops_lammps"  #TODO: modify this in the controller?


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


class EngineWriter(object):
    def __init__(self, script):
        self.script = script
        # TODO: don't hard-code these
        self.options = {'n_steps_per_frame': 200,
                        'n_frames_max': 500000}

    @property
    def code(self):
        lines = "with open('" + self.script + "', 'r') as f:\n"
        lines += "    data = f.read()\n"
        lines += "engine = ops_lammps.Engine(inputs=data, options="
        lines += str(self.options) + ")\n"
        return lines


class RandomizerWriter(object):
    pass
