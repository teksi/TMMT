class ModulesRegistry:
    """
    A registry to manage and keep track of modules in the Teksi Module Management Tool.
    """

    def __init__(self):
        self._modules = {}

    def register_module(self, module):
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' is already registered.")
        self._modules[module.name] = module

    def unregister_module(self, name):
        if name not in self._modules:
            raise KeyError(f"Module '{name}' is not registered.")
        del self._modules[name]

    def get_module(self, name):
        if name not in self._modules:
            raise KeyError(f"Module '{name}' is not registered.")
        return self._modules[name]

    def modules(self):
        return list(self._modules.values())
