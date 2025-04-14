class Module:
    def __init__(self, name: str, version: str):
        self.name = name
        self.url = version
        self.versions = []

    def __repr__(self):
        return f"Module(name={self.name}, url={self.url})"
