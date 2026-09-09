import uuid
from datetime import date, datetime, time

from models.task import Task


class Project:
    """
    Represents one project.

    The project deadline is stored as a datetime so the
    application can calculate the exact remaining time.

    Example:

        2026-09-14 23:30
    """

    def __init__(
        self,
        name,
        start_date,
        deadline,
        tasks=None,
        id=None,
        description="",
        deadline_time=None
    ):


        # Basic validation
    

        if not name or not name.strip():
            raise ValueError(
                "Project name cannot be empty."
            )

        # Make sure start_date is datetime.
        start_date = self._make_datetime(
            start_date
        )

        # Make sure deadline is datetime.
        deadline = self._make_datetime(
            deadline,
            deadline_time
        )

        if start_date >= deadline:
            raise ValueError(
                "Start date must be before deadline."
            )

        if tasks is None:
            tasks = []

 
        # Project information
   

        self.id = (
            id
            if id is not None
            else str(uuid.uuid4())
        )

        self.name = name.strip()

        self.description = description

        self.start_date = start_date

        self.deadline = deadline

        self.tasks = tasks

   
    @staticmethod
    def _make_datetime(
        value,
        deadline_time=None
    ):
        """
        Convert date/datetime/string values into datetime.

        This keeps the Project class compatible with older data.
        """

        # Already a datetime.
        if isinstance(value, datetime):

            return value

        # A date without time.
        if isinstance(value, date):

            if deadline_time is None:

                return datetime.combine(
                    value,
                    time.min
                )

            hour, minute = map(
                int,
                deadline_time.split(":")
            )

            return datetime.combine(
                value,
                time(
                    hour,
                    minute
                )
            )

        # String support.
        if isinstance(value, str):

            try:

                return datetime.fromisoformat(
                    value
                )

            except ValueError:

                parsed_date = date.fromisoformat(
                    value
                )

                if deadline_time is None:

                    return datetime.combine(
                        parsed_date,
                        time.min
                    )

                hour, minute = map(
                    int,
                    deadline_time.split(":")
                )

                return datetime.combine(
                    parsed_date,
                    time(
                        hour,
                        minute
                    )
                )

        raise TypeError(
            "Date value must be date, datetime or ISO string."
        )


    # DEADLINE TIME


    @property
    def deadline_time(self):
        """
        Return deadline time as HH:MM.
        """

        return self.deadline.strftime(
            "%H:%M"
        )


    # TASK MANAGEMENT


    def add_task(self, task):

        self.tasks.append(
            task
        )

    def remove_task(
        self,
        task_id
    ):

        for task in self.tasks:

            if task.id == task_id:

                self.tasks.remove(
                    task
                )

                return

        raise ValueError(
            f"Task '{task_id}' not found."
        )

    def get_task(
        self,
        task_id
    ):

        for task in self.tasks:

            if task.id == task_id:

                return task

        return None

    def update_task(
        self,
        task_id,
        new_title=None,
        new_weight=None,
        new_deadline=None,
        new_progress=None
    ):

        task = self.get_task(
            task_id
        )

        if task is None:

            raise ValueError(
                f"Task '{task_id}' not found."
            )

        if new_title is not None:

            new_title = new_title.strip()

            if not new_title:

                raise ValueError(
                    "Task title cannot be empty."
                )

            task.title = new_title

        if new_weight is not None:

            new_weight = float(
                new_weight
            )

            if new_weight < 1 or new_weight > 10:

                raise ValueError(
                    "Task weight must be between 1 and 10."
                )

            task.weight = new_weight

        if new_deadline is not None:

            task.deadline = new_deadline

        if new_progress is not None:

            task.update_progress(
                new_progress
            )


    # TASK FILTERS


    def get_completed_tasks(self):

        result = []

        for task in self.tasks:

            if task.is_completed():

                result.append(
                    task
                )

        return result

    def get_pending_tasks(self):

        result = []

        for task in self.tasks:

            if not task.is_completed():

                result.append(
                    task
                )

        return result

    # STORAGE


    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,

            # Exact datetime is saved.
            "start_date": self.start_date.isoformat(),

            "deadline": self.deadline.isoformat(),

            "tasks": [
                task.to_dict()
                for task in self.tasks
            ]
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):

        tasks = [
            Task.from_dict(
                task_data
            )
            for task_data in data.get(
                "tasks",
                []
            )
        ]

        # Backward compatibility


        old_deadline = data["deadline"]

        project_deadline = datetime.fromisoformat(
            old_deadline
        )

        old_start = data["start_date"]

        try:

            project_start = datetime.fromisoformat(
                old_start
            )

        except ValueError:

            project_start = date.fromisoformat(
                old_start
            )

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get(
                "description",
                ""
            ),
            start_date=project_start,
            deadline=project_deadline,
            tasks=tasks
        )