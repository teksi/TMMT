from qgis.PyQt.QtCore import QDateTime, Qt


class ModuleVersion:
    def __init__(self, json_payload: dict):

        self.name = json_payload["name"]
        self.created_at = QDateTime.fromString(json_payload["created_at"], Qt.ISODate)
        self.prerelease = json_payload["prerelease"]
        self.html_url = json_payload["html_url"]

    def display_name(self):
        if self.prerelease:
            return f"{self.name} (prerelease)"

        return self.name
