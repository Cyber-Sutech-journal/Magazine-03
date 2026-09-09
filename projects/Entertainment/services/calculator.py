from datetime import date, datetime, timedelta


class Calculator:
    """
    Main calculation class.

    Project deadline calculations use the exact deadline
    datetime whenever possible.
    """


    # DATETIME HELPERS
 

    @staticmethod
    def get_current_datetime():

        return datetime.now()

    @staticmethod
    def get_project_start_datetime(
        project
    ):
        """
        Return project start as datetime.
        """

        if isinstance(
            project.start_date,
            datetime
        ):

            return project.start_date

        return datetime.combine(
            project.start_date,
            datetime.min.time()
        )

    @staticmethod
    def get_project_deadline_datetime(
        project
    ):
        """
        Return project deadline as datetime.

        Supports both old date values and new datetime values.
        """

        if isinstance(
            project.deadline,
            datetime
        ):

            return project.deadline

        return datetime.combine(
            project.deadline,
            datetime.min.time()
        )

    
    # PROJECT PROGRESS
 

    @staticmethod
    def calculate_project_progress(
        project
    ):
        """
        Calculate project progress.

        If there are no tasks, the project has no task-based
        progress and returns 0.

        When a manual project progress system is added,
        this section can use that value.
        """

        if not project.tasks:

            return 0.0

        total_weight = sum(
            float(task.weight)
            for task in project.tasks
        )

        if total_weight <= 0:

            return 0.0

        weighted_progress = sum(
            float(task.weight)
            * float(task.progress_percent)
            for task in project.tasks
        )

        progress = (
            weighted_progress
            / total_weight
        )

        return max(
            0.0,
            min(
                100.0,
                progress
            )
        )

  
    # TOTAL PROJECT TIME
   

    @staticmethod
    def calculate_total_project_time(
        project
    ):
        """
        Return the complete project duration as timedelta.
        """

        start = (
            Calculator.get_project_start_datetime(
                project
            )
        )

        deadline = (
            Calculator.get_project_deadline_datetime(
                project
            )
        )

        return (
            deadline
            - start
        )

   
    # TOTAL PROJECT DAYS
  

    @staticmethod
    def calculate_total_project_days(
        project
    ):
        """
        Return total project duration in days.

        Fractional days are allowed because the deadline
        can now contain an exact time.
        """

        total_time = (
            Calculator.calculate_total_project_time(
                project
            )
        )

        return total_time.total_seconds() / 86400

   
    # ELAPSED TIME
   

    @staticmethod
    def calculate_elapsed_time(
        project,
        now=None
    ):
        """
        Return exact elapsed time as timedelta.
        """

        if now is None:

            now = datetime.now()

        start = (
            Calculator.get_project_start_datetime(
                project
            )
        )

        if now <= start:

            return timedelta(0)

        return (
            now - start
        )

    
    # ELAPSED DAYS
  

    @staticmethod
    def calculate_time_elapsed(
        project,
        today=None
    ):
        """
        Return elapsed time in decimal days.

        Keeps the old method name so existing UI code
        continues to work.
        """

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            # Testing with a date.
            now = datetime.combine(
                today,
                datetime.min.time()
            )

        elapsed_time = (
            Calculator.calculate_elapsed_time(
                project,
                now
            )
        )

        return (
            elapsed_time.total_seconds()
            / 86400
        )

 
    # REMAINING TIME
    

    @staticmethod
    def calculate_remaining_time(
        project,
        now=None
    ):
        """
        Return exact time remaining until deadline.

        Positive:
            Time remaining.

        Negative:
            Deadline has passed.
        """

        if now is None:

            now = datetime.now()

        elif isinstance(
            now,
            date
        ) and not isinstance(
            now,
            datetime
        ):

            now = datetime.combine(
                now,
                datetime.min.time()
            )

        deadline = (
            Calculator.get_project_deadline_datetime(
                project
            )
        )

        return (
            deadline
            - now
        )

 
    # REMAINING DAYS
    @staticmethod
    def calculate_time_remaining(
        project,
        today=None
    ):
        """
        Return remaining time as decimal days.

        Example:

            2.5 = 2 days and 12 hours remaining.

        Negative means overdue.
        """

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            now = datetime.combine(
                today,
                datetime.min.time()
            )

        remaining = (
            Calculator.calculate_remaining_time(
                project,
                now
            )
        )

        return (
            remaining.total_seconds()
            / 86400
        )

    # REMAINING HOURS
    @staticmethod
    def calculate_remaining_hours(
        project,
        now=None
    ):
        """
        Return exact remaining hours.
        """

        remaining = (
            Calculator.calculate_remaining_time(
                project,
                now
            )
        )

        return (
            remaining.total_seconds()
            / 3600
        )


    # REMAINING MINUTES
   

    @staticmethod
    def calculate_remaining_minutes(
        project,
        now=None
    ):
        """
        Return exact remaining minutes.
        """

        remaining = (
            Calculator.calculate_remaining_time(
                project,
                now
            )
        )

        return (
            remaining.total_seconds()
            / 60
        )

 
    # FORMATTED REMAINING TIME


    @staticmethod
    def format_remaining_time(
        project,
        now=None
    ):
        """
        Return a human-readable exact remaining time.

        Example:

            7 days, 22 hours, 12 minutes remaining
        """

        if now is None:

            now = datetime.now()

        remaining = (
            Calculator.calculate_remaining_time(
                project,
                now
            )
        )

        total_seconds = int(
            remaining.total_seconds()
        )

    
        # Overdue
    

        if total_seconds < 0:

            total_seconds = abs(
                total_seconds
            )

            days = (
                total_seconds
                // 86400
            )

            total_seconds %= 86400

            hours = (
                total_seconds
                // 3600
            )

            total_seconds %= 3600

            minutes = (
                total_seconds
                // 60
            )

            return (
                f"{days}d {hours}h {minutes}m overdue"
            )

  
        # Remaining
  

        days = (
            total_seconds
            // 86400
        )

        total_seconds %= 86400

        hours = (
            total_seconds
            // 3600
        )

        total_seconds %= 3600

        minutes = (
            total_seconds
            // 60
        )

        return (
            f"{days}d {hours}h {minutes}m remaining"
        )


    # TIME PROGRESS
 

    @staticmethod
    def calculate_time_progress(
        project,
        today=None
    ):
        """
        Calculate exact percentage of project time used.
        """

        total_time = (
            Calculator.calculate_total_project_time(
                project
            )
        )

        if total_time.total_seconds() <= 0:

            return 0.0

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            now = datetime.combine(
                today,
                datetime.min.time()
            )

        elapsed_time = (
            Calculator.calculate_elapsed_time(
                project,
                now
            )
        )

        progress = (
            elapsed_time.total_seconds()
            / total_time.total_seconds()
        ) * 100

        return max(
            0.0,
            min(
                100.0,
                progress
            )
        )


    # SCHEDULE GAP


    @staticmethod
    def calculate_schedule_gap(
        project,
        today=None
    ):
        """
        Time Progress - Project Progress.

        Positive:
            Behind schedule.

        Negative:
            Ahead of schedule.
        """

        project_progress = (
            Calculator.calculate_project_progress(
                project
            )
        )

        time_progress = (
            Calculator.calculate_time_progress(
                project,
                today
            )
        )

        return (
            time_progress
            - project_progress
        )

    # PROJECT STATUS


    @staticmethod
    def get_project_status(
        project,
        today=None
    ):
        """
        Determine project status using the exact deadline time.
        """

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            now = datetime.combine(
                today,
                datetime.min.time()
            )

        progress = (
            Calculator.calculate_project_progress(
                project
            )
        )

        if progress >= 100:

            return "completed"

        deadline = (
            Calculator.get_project_deadline_datetime(
                project
            )
        )

        if now > deadline:

            return "overdue"

        if progress <= 0:

            return "not_started"

        return "in_progress"

    # IS PROJECT OVERDUE


    @staticmethod
    def is_project_overdue(
        project,
        today=None
    ):

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            now = datetime.combine(
                today,
                datetime.min.time()
            )

        progress = (
            Calculator.calculate_project_progress(
                project
            )
        )

        if progress >= 100:

            return False

        deadline = (
            Calculator.get_project_deadline_datetime(
                project
            )
        )

        return (
            now > deadline
        )

 
    # DISASTER INDEX
 

    @staticmethod
    def calculate_disaster_index(
        project,
        today=None
    ):
        """
        Calculate Disaster Index.

        Uses exact time instead of only calendar days.
        """

        if today is None:

            now = datetime.now()

        elif isinstance(
            today,
            datetime
        ):

            now = today

        else:

            now = datetime.combine(
                today,
                datetime.min.time()
            )

        project_progress = (
            Calculator.calculate_project_progress(
                project
            )
        )

        # Completed project = zero risk.
        if project_progress >= 100:

            return 0.0

        time_progress = (
            Calculator.calculate_time_progress(
                project,
                now
            )
        )

        schedule_gap = (
            time_progress
            - project_progress
        )

        positive_gap = max(
            schedule_gap,
            0.0
        )

        gap_score = (
            positive_gap
            / 100
        ) * 50

        # No tasks
   

        if not project.tasks:

            return max(
                0.0,
                min(
                    100.0,
                    gap_score
                )
            )

        # Overdue tasks
       

        overdue_tasks = []

        for task in project.tasks:

            if task.deadline is None:

                continue

            if task.is_completed():

                continue

            # Support old date deadlines.
            task_deadline = task.deadline

            if isinstance(
                task_deadline,
                datetime
            ):

                is_overdue = (
                    task_deadline
                    < now
                )

            else:

                is_overdue = (
                    task_deadline
                    < now.date()
                )

            if is_overdue:

                overdue_tasks.append(
                    task
                )

        overdue_task_ratio = (
            len(overdue_tasks)
            / len(project.tasks)
        )

        task_score = (
            overdue_task_ratio
            * 30
        )

        total_weight = sum(
            float(task.weight)
            for task in project.tasks
        )

        overdue_weight = sum(
            float(task.weight)
            for task in overdue_tasks
        )

        if total_weight > 0:

            overdue_weight_ratio = (
                overdue_weight
                / total_weight
            )

        else:

            overdue_weight_ratio = 0.0

        weight_score = (
            overdue_weight_ratio
            * 20
        )

        disaster_index = (
            gap_score
            + task_score
            + weight_score
        )

        return max(
            0.0,
            min(
                100.0,
                disaster_index
            )
        )

    # DISASTER LEVEL


    @staticmethod
    def get_disaster_level(
        disaster_index
    ):

        if disaster_index <= 30:

            return "safe"

        if disaster_index <= 70:

            return "warning"

        return "danger"