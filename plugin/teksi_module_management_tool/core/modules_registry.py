class ModulesRegistry:
    """
    A registry to manage and keep track of modules in the Teksi Module Management Tool.
    """

    def __init__(self):
        self._modules = {}

    def register_module(self, name, module):
        if name in self._modules:
            raise ValueError(f"Module '{name}' is already registered.")
        self._modules[name] = module

    def unregister_module(self, name):
        if name not in self._modules:
            raise KeyError(f"Module '{name}' is not registered.")
        del self._modules[name]

    def get_module(self, name):
        if name not in self._modules:
            raise KeyError(f"Module '{name}' is not registered.")
        return self._modules[name]

    def list_modules(self):
        return list(self._modules.keys())
