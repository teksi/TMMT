from qgis.PyQt.QtCore import QDateTime, Qt
import requests
import os


class ModuleVersion:

    # enum for version type
    class Type:
        RELEASE = "release"
        BRANCH = "branch"

    def __init__(self, organisation, repository, json_payload: dict, type = Type.RELEASE):

        self.type = type
        self.name = json_payload["name"]
        self.created_at = None
        self.prerelease = False
        self.html_url = None
        self.download_url = f"https://github.com/{organisation}/{repository}/archive/refs/heads/{self.name}.zip"

        if self.type == ModuleVersion.Type.RELEASE:
            self.__parse_release(json_payload)
        elif self.type == ModuleVersion.Type.BRANCH:
            self.__parse_branch(json_payload)
        else:
            raise ValueError(f"Unknown type '{type}'")

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
        self.created_at = QDateTime.fromString(json_payload["created_at"], Qt.ISODate)
        self.prerelease = json_payload["prerelease"]
        self.html_url = json_payload["html_url"]

    def __parse_branch(self, json_payload: dict):
        pass

