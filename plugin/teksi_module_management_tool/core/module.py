import requests

from .module_version import ModuleVersion


class Module:
    def __init__(self, name: str, organisation: str, repository: str):
        self.name = name
        self.organisation = organisation
        self.repository = repository
        self.versions = []
        self.development_versions = []
        self.latest_version = None

    def __repr__(self):
        return f"Module(name={self.name}, organisation={self.organisation}, repository={self.repository})"

    def load_versions(self):
        r = requests.get(
            f"https://api.github.com/repos/{self.organisation}/{self.repository}/releases"
        )

        # Raise an exception in case of http errors
        r.raise_for_status()

        json_versions = r.json()
        self.versions = []
        self.latest_version = None
        for json_version in json_versions:
            module_version = ModuleVersion(organisation=self.organisation, repository=self.repository, json_payload=json_version, type=ModuleVersion.Type.RELEASE)
            self.versions.append(module_version)

            # Latest version -> most recent commit date for non prerelease
            if module_version.prerelease is True:
                continue

            if self.latest_version is None:
                self.latest_version = module_version
                continue

            if module_version.created_at > self.latest_version.created_at:
                self.latest_version = module_version

    def load_development_versions(self):

        self.development_versions = []
        
        # Create version for the main branch
        mainVersion = ModuleVersion(organisation=self.organisation, repository=self.repository, json_payload=str(), type=ModuleVersion.Type.BRANCH, name="main", branch="main")
        self.development_versions.append(mainVersion)

        # Load versions from pull requests
        r = requests.get(
            f"https://api.github.com/repos/{self.organisation}/{self.repository}/pulls"
        )

        # Raise an exception in case of http errors
        r.raise_for_status()

        json_versions = r.json()
        for json_version in json_versions:
            module_version = ModuleVersion(organisation=self.organisation, repository=self.repository, json_payload=json_version, type=ModuleVersion.Type.PULL_REQUEST)
            self.development_versions.append(module_version)

