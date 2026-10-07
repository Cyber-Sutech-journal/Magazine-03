class ProjectManager:
    """
    This class manages all projects in the application.
    """

    def __init__(self):
        # List of all projects
        self.projects = []

    # Add Project
 

    def add_project(self, project):
        """
        Add a new project to the project list.

        Project IDs must be unique.
        """

        # Check if a project with this ID already exists
        if self.get_project(project.id) is not None:
            raise ValueError("A project with this ID already exists.")

        self.projects.append(project)

    # Remove Project


    def remove_project(self, project_id):
        """
        Remove a project using its ID.

        Returns:
            True  -> project was removed
            False -> project was not found
        """

        project = self.get_project(project_id)

        if project is None:
            return False

        self.projects.remove(project)

        return True

    # Get Project


    def get_project(self, project_id):
        """
        Find and return a project using its ID.

        Returns:
            Project object if found
            None if the project does not exist
        """

        for project in self.projects:

            if project.id == project_id:
                return project

        return None


    # Get All Projects
   

    def get_all_projects(self):
        """
        Return a list containing all projects.

        A copy of the list is returned so that other parts
        of the program cannot directly change the main list.
        """

        return self.projects.copy()


    # Search Project


    def search_project(self, query):
        """
        Search for projects by name or description.

        The search is not case-sensitive.

        Example:
            search_project("python")

        can find:
            "Python Game"
            "PYTHON Project"
            "Learning Python"
        """

        
        if not isinstance(query, str):
            raise TypeError("Search query must be a string.")

        query = query.strip().casefold()

        # If the search box is empty,
        # return all projects.
        if query == "":
            return self.get_all_projects()

        results = []

        for project in self.projects:

            project_name = project.name.casefold()
            project_description = project.description.casefold()

            # Check the name and description
            if query in project_name or query in project_description:
                results.append(project)

        return results

    # Check Project Existence


    def project_exists(self, project_id):
        """
        Check if a project with the given ID exists.

        Returns:
            True  -> project exists
            False -> project does not exist
        """

        return self.get_project(project_id) is not None

    # Count Projects
    def project_count(self):
        """
        Return the number of projects.
        """

        return len(self.projects)

  
    # Clear Projects
    

    def clear_projects(self):
        """
        Remove all projects from memory.

        Note:
            This does not delete the JSON file.
            Saving and deleting files will be handled
            by the Storage class.
        """

        self.projects.clear()

 
    # Replace All Projects
  

    def set_projects(self, projects):
        """
        Replace the current project list with a new list.

        This method will mainly be used by the Storage class
        when projects are loaded from the JSON file.
        """

        # Check for duplicate IDs
        project_ids = []

        for project in projects:

            if project.id in project_ids:
                raise ValueError(
                    "Two projects cannot have the same ID."
                )

            project_ids.append(project.id)

        # Replace the old list
        self.projects = projects.copy()
