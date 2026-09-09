import json
import os
from pathlib import Path
from datetime import datetime


class JSONStorage:
    """
    This class is responsible for saving and loading projects
    from a JSON file.

    The Storage class does not calculate project progress,
    time, status, disaster index, or prediction.

    It only saves and loads data.
    """
    """just in case!!!!"""
    CURRENT_VERSION = 1

    def __init__(self, file_path=None):
        """
        Create a storage object.

        Args:
            file_path:
                Optional custom file path.

                This is useful for testing.

                If no path is given, the application uses
                the Windows APPDATA directory.
        """

        if file_path is None:
            self.file_path = self.get_default_file_path()
        else:
            self.file_path = Path(file_path)

        # Make sure the parent directory exists.
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )
    # GET DEFAULT DATA DIRECTORY

    @staticmethod
    def get_data_directory():
        """
        Return the directory where application data should be stored.

        On Windows, APPDATA is used.

        Example:

            C:/Users/Username/AppData/Roaming/ProjectLateAgain
        """

        appdata = os.environ.get("APPDATA")

        if appdata:
            data_directory = (
                Path(appdata) / "ProjectLateAgain"
            )
        else:
            # Fallback for systems where APPDATA is not available.
            data_directory = (
                Path.home() / ".project_late_again"
            )

        # Create the directory if it does not exist.
        data_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return data_directory
    # GET DEFAULT FILE PATH

    @classmethod
    def get_default_file_path(cls):
        """
        Return the default path of the projects JSON file.
        """

        data_directory = cls.get_data_directory()

        return data_directory / "projects.json"
    # SAVE PROJECTS

    def save_projects(self, projects):
        """
        Save a list of Project objects to the JSON file.

        Only raw project/task data should be stored.

        Calculated values such as:
            - project progress
            - time progress
            - disaster index
            - status
            - prediction

        are NOT stored.
        """

        if not isinstance(projects, list):
            raise TypeError(
                "Projects must be provided as a list."
            )

        # Convert every Project object into a dictionary.
        project_data = []

        for project in projects:
            project_data.append(
                project.to_dict()
            )

        # Create the final JSON structure.
        data = {
            "version": self.CURRENT_VERSION,
            "projects": project_data
        }

        # Temporary file path.
        temporary_file = self.file_path.with_suffix(
            ".tmp"
        )

        try:
            # Write the new data into a temporary file first.
            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

                # Make sure all data is written to the file.
                file.flush()
                os.fsync(file.fileno())

            # Replace the old file with the new file.
            temporary_file.replace(self.file_path)

        except Exception:
            # If something goes wrong, try to remove
            # the temporary file.
            if temporary_file.exists():
                temporary_file.unlink()

            # Send the error to the caller.
            raise
    # LOAD PROJECTS

    def load_projects(self):
        """
        Load projects from the JSON file.

        Returns:
            A list of Project objects.

        If the file does not exist:
            return an empty list.

        If the JSON file is corrupted:
            create a backup and return an empty list.
        """

        # First run:
        # There is no JSON file yet.
        if not self.file_path.exists():
            return []

        try:
            # Read the JSON file.
            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except (json.JSONDecodeError, OSError):
            """
            The file is corrupted or cannot be read.

            We create a backup instead of deleting it.
            """

            self._backup_corrupted_file()

            return []

        # Check the structure of the JSON file.
        if not isinstance(data, dict):
            self._backup_corrupted_file()
            return []

        # Get version.
        version = data.get(
            "version",
            self.CURRENT_VERSION
        )

        if version != self.CURRENT_VERSION:
            self._backup_corrupted_file()

            return []

        # Get projects.
        projects_data = data.get(
            "projects",
            []
        )

        if not isinstance(projects_data, list):
            self._backup_corrupted_file()

            return []

        projects = []

        try:

            for project_data in projects_data:

                project = self._load_project(
                    project_data
                )

                projects.append(project)

        except (TypeError, ValueError, KeyError):

            # Something inside the JSON structure is invalid.
            self._backup_corrupted_file()

            return []

        return projects

    # LOAD ONE PROJECT

    @staticmethod
    def _load_project(project_data):
        """
        Convert a dictionary into a Project object.

        Project.from_dict() is responsible for reconstructing
        the Project and its Tasks.
        """

        if not isinstance(project_data, dict):
            raise TypeError(
                "Invalid project data."
            )

        # Import here to reduce circular-import problems.
        from models.project import Project

        return Project.from_dict(project_data)
    # BACKUP CORRUPTED FILE


    def _backup_corrupted_file(self):
        """
        Create a backup of a corrupted JSON file.

        Example:

            projects.json
            projects.corrupted_20260902_153000.json
        """

        if not self.file_path.exists():
            return

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_name = (
            f"projects.corrupted_{timestamp}.json"
        )

        backup_path = (
            self.file_path.parent / backup_name
        )

        try:
            self.file_path.replace(backup_path)

        except OSError:
            # If backup creation fails,
            # do not crash the whole application.
            pass
    # CHECK FILE EXISTS
    def file_exists(self):
        """
        Check whether the JSON file exists.
        """

        return self.file_path.exists()
    # DELETE DATA FILE

    def delete_data_file(self):
        """
        Delete the JSON data file.

        This method should be used carefully.

        It is mainly useful for testing or resetting
        the application data.
        """

        if not self.file_path.exists():
            return False

        self.file_path.unlink()

        return True
    # GET FILE PATH

    def get_file_path(self):
        """
        Return the current JSON file path.
        """

        return self.file_path
