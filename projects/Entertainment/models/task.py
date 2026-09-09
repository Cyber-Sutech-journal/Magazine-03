from models.enums import TaskStatus
from datetime import datetime, date, time
import uuid


class Task:
    def __init__(
        self,
        title,
        weight,
        progress_percent=0,
        status=TaskStatus.TODO,
        completed_at=None,
        deadline=None,
        id=None
    ):

        # Weight must be greater than zero.
        if weight <= 0:
            raise ValueError(
                "Task Weight Must Be Greater Than Zero"
            )


        # ID
        

        self.id = (
            id
            if id is not None
            else str(uuid.uuid4())
        )

        self.title = title

        self.weight = weight

        self.progress_percent = max(
            0,
            min(
                100,
                progress_percent
            )
        )

        self.status = status

        self.completed_at = completed_at

        # Deadline can now contain date + time.
        self.deadline = self._convert_deadline(
            deadline
        )

    # DEADLINE CONVERSION
  

    @staticmethod
    def _convert_deadline(deadline):
        """
        Convert deadline to datetime.

        Supports:
        - datetime
        - date
        - ISO datetime string
        - ISO date string
        - None
        """

        if deadline is None:
            return None

        # Already datetime.
        if isinstance(
            deadline,
            datetime
        ):
            return deadline

        # Old date-only value.
        if isinstance(
            deadline,
            date
        ):

            return datetime.combine(
                deadline,
                time.min
            )

        # String value.
        if isinstance(
            deadline,
            str
        ):

            try:

                return datetime.fromisoformat(
                    deadline
                )

            except ValueError:

                old_date = date.fromisoformat(
                    deadline
                )

                return datetime.combine(
                    old_date,
                    time.min
                )

        raise TypeError(
            "Deadline must be date, datetime, string or None."
        )

   
    # START
 

    def start(self):

        if self.status == TaskStatus.COMPLETED:

            return

        self.status = TaskStatus.IN_PROGRESS


    # COMPLETE
   

    def complete(self):

        if self.status == TaskStatus.COMPLETED:

            return

        self.status = TaskStatus.COMPLETED

        self.progress_percent = 100

        self.completed_at = datetime.now()

    
    # REOPEN
   

    def reopen(self):

        if self.status != TaskStatus.COMPLETED:

            return

        self.status = TaskStatus.REOPENED

        self.progress_percent = 0

        self.completed_at = None

   
    # UPDATE PROGRESS
  

    def update_progress(
        self,
        percent
    ):

        # Clamp progress between 0 and 100.
        percent = max(
            0,
            min(
                100,
                float(percent)
            )
        )

        if percent == 0:

            self.status = TaskStatus.TODO

            self.progress_percent = 0

            self.completed_at = None

        elif 1 <= percent <= 99:

            self.status = TaskStatus.IN_PROGRESS

            self.progress_percent = percent

            self.completed_at = None

        elif percent == 100:

            self.complete()


    # CHECK COMPLETION
  

    def is_completed(self):

        return (
            self.status
            == TaskStatus.COMPLETED
        )

    # CHECK OVERDUE
 

    def is_overdue(
        self,
        current_time=None
    ):
        """
        Check whether the task deadline has passed.

        The comparison is now done using exact time.
        """

        if self.deadline is None:

            return False

        if self.is_completed():

            return False

        if current_time is None:

            current_time = datetime.now()

        elif isinstance(
            current_time,
            date
        ) and not isinstance(
            current_time,
            datetime
        ):

            current_time = datetime.combine(
                current_time,
                time.min
            )

        return (
            self.deadline
            < current_time
        )

  
    # STORAGE
  

    def to_dict(self):

        return {
            "id": self.id,

            "title": self.title,

            "weight": self.weight,

            "progress_percent": (
                self.progress_percent
            ),

            "status": self.status.value,

            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at is not None
                else None
            ),

            # Save exact deadline date + time.
            "deadline": (
                self.deadline.isoformat()
                if self.deadline is not None
                else None
            )
        }


    # LOAD FROM JSON
 
    @classmethod
    def from_dict(
        cls,
        data
    ):

        completed_at = None

        if data.get(
            "completed_at"
        ) is not None:

            completed_at = (
                datetime.fromisoformat(
                    data["completed_at"]
                )
            )

        deadline = None

        if data.get(
            "deadline"
        ) is not None:

            deadline = (
                cls._convert_deadline(
                    data["deadline"]
                )
            )

        return cls(

            id=data.get(
                "id"
            ),

            title=data["title"],

            weight=data["weight"],

            progress_percent=data.get(
                "progress_percent",
                0
            ),

            status=TaskStatus(
                data.get(
                    "status",
                    TaskStatus.TODO.value
                )
            ),

            completed_at=completed_at,

            deadline=deadline
        )