from typing import Callable

class LazyObject:
    def __init__(self, get_obj_func: Callable):
        """
        LazyObject defers the creation of an object to when it will be used, this is useful to handle cases where
        the consumer will only touch a handful of objects (such as images) and we want to preserve the appearance of
        swift processing.
        ""

        :param get_obj_func: function to call to get the object, should be pre-parametrized
        :type get_obj_func: Callable
        """
        self.get_obj_func = get_obj_func
        self.obj = None

    def __getattr__(self, *args, **kwargs):
        if not self.obj:
            self.obj = self.get_obj_func()
        return self.obj.__getattr__(*args, **kwargs)

    def __setattr__(self, *args, **kwargs):
        if not self.obj:
            self.obj = self.get_obj_func()
        return self.obj.__setattr__(*args, **kwargs)
