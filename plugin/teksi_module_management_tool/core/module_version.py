import os

import requests
from qgis.PyQt.QtCore import QDateTime, Qt


class ModuleVersion:

    # enum for version type
    class Type:
        RELEASE = "release"
        BRANCH = "branch"
        PULL_REQUEST = "pull_request"

    def __init__(
        self,
        organisation,
        repository,
        json_payload: dict,
        type=Type.RELEASE,
        name=None,
        branch=None,
    ):

        self.type = type
        self.name = name
        self.branch = branch
        self.created_at = None
        self.prerelease = False
        self.html_url = None

        if self.type == ModuleVersion.Type.RELEASE:
            self.__parse_release(json_payload)
        elif self.type == ModuleVersion.Type.BRANCH:
            pass
        elif self.type == ModuleVersion.Type.PULL_REQUEST:
            self.__parse_pull_request(json_payload)
        else:
            raise ValueError(f"Unknown type '{type}'")

        type = "heads"
        if self.type == ModuleVersion.Type.RELEASE:
            type = "tags"

        # self.download_url = f"https://github.com/{organisation}/{repository}/archive/refs/{type}/{self.branch}.zip"
        self.download_url = (
            f"https://codeload.github.com/teksi/wastewater/zip/refs/tags/{self.branch}"
        )

    def display_name(self):
        if self.prerelease:
            return f"{self.name} (prerelease)"

        return self.name

    def download_zip(self, destination_directory: str):
        # Define the directory and file path
        os.makedirs(destination_directory, exist_ok=True)
        file_path = os.path.join(destination_directory, f"{self.name}.zip")

        # Download the file
        r = requests.get(self.download_url, allow_redirects=True)

        # Raise an exception in case of http errors
        r.raise_for_status()

        # Save the content to the specified file
        with open(file_path, "wb") as file:
            file.write(r.content)

        return file_path

    def __parse_release(self, json_payload: dict):
        if self.name is None:
            self.name = json_payload["name"]
        self.branch = self.name
        self.created_at = QDateTime.fromString(json_payload["created_at"], Qt.ISODate)
        self.prerelease = json_payload["prerelease"]
        self.html_url = json_payload["html_url"]

    def __parse_pull_request(self, json_payload: dict):
        if self.name is None:
            self.name = f"#{json_payload['number']} {json_payload['title']}"
        self.branch = json_payload["head"]["ref"]
        self.created_at = QDateTime.fromString(json_payload["created_at"], Qt.ISODate)
        self.prerelease = False
        self.html_url = json_payload["html_url"]
