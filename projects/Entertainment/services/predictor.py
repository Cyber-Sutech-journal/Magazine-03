from datetime import date, timedelta
import math

from services.calculator import Calculator


class Predictor:
    """
    This class predicts when a project is expected to be completed.

    The prediction is based on the average project progress
    from the project start date until today.

    Example:

        Project Progress = 40%
        Time Elapsed = 10 days

        Progress Rate = 4% per day

        Remaining Progress = 60%

        Estimated Remaining Time = 60 / 4 = 15 days
    """

  
    # Calculate Progress Rate
 

    @staticmethod
    def calculate_progress_rate(project, today=None):
        """
        Calculate the average project progress per day.

        Formula:

            progress_rate =
                project_progress / elapsed_days

        Example:

            Progress = 40%
            Elapsed = 10 days

            Rate = 4% per day

        Returns:
            Progress rate as a float.

            Returns None if there is not enough information
            to calculate a valid rate.
        """

        # Use today's date if no date was provided.
        if today is None:
            today = date.today()

        # Get the current project progress.
        project_progress = Calculator.calculate_project_progress(
            project
        )

        # Get the number of elapsed days.
        elapsed_days = Calculator.calculate_time_elapsed(
            project,
            today
        )

        # We cannot divide by zero.
        if elapsed_days <= 0:
            return None

        # If project has no progress yet,
        # there is no useful rate for prediction.
        if project_progress <= 0:
            return None

        # A completed project does not need prediction.
        if project_progress >= 100:
            return None

        # Calculate average progress per day.
        progress_rate = (
            project_progress / elapsed_days
        )

        # Protect against invalid values.
        if progress_rate <= 0:
            return None

        return progress_rate

  
    # Calculate Remaining Progress


    @staticmethod
    def calculate_remaining_progress(project):
        """
        Calculate how much project progress is still remaining.

        Example:

            Project Progress = 65%

            Remaining Progress = 35%

        Returns:
            Remaining progress between 0 and 100.
        """

        project_progress = Calculator.calculate_project_progress(
            project
        )

        remaining_progress = 100.0 - project_progress

        # Keep the result between 0 and 100.
        remaining_progress = max(
            0.0,
            min(100.0, remaining_progress)
        )

        return remaining_progress

    # Calculate Estimated Remaining Days 
    @staticmethod
    def calculate_remaining_days(project, today=None):
        """
        Estimate how many more days are needed to finish the project.

        Formula:

            remaining_days =
                remaining_progress / progress_rate

        Returns:
            Estimated number of remaining days as a float.

            Returns None if prediction is not possible.
        """

        if today is None:
            today = date.today()

        # Calculate current progress.
        project_progress = Calculator.calculate_project_progress(
            project
        )

        # Completed project does not need prediction.
        if project_progress >= 100:
            return None

        # Calculate average progress rate.
        progress_rate = Predictor.calculate_progress_rate(
            project,
            today
        )

        # No valid rate means no prediction.
        if progress_rate is None:
            return None

        # Calculate remaining project work.
        remaining_progress = (
            Predictor.calculate_remaining_progress(project)
        )

        # Safety check.
        if remaining_progress <= 0:
            return 0.0

        # Calculate estimated remaining days.
        remaining_days = (
            remaining_progress / progress_rate
        )

        return remaining_days


    # Predict Completion Date


    @staticmethod
    def predict_completion_date(project, today=None):
        """
        Predict the date when the project is expected to reach 100%.

        Returns:
            A date object containing the predicted completion date.

            Returns None if prediction is not possible.
        """

        if today is None:
            today = date.today()

        # Calculate remaining days.
        remaining_days = Predictor.calculate_remaining_days(
            project,
            today
        )

        # No prediction available.
        if remaining_days is None:
            return None

        # Convert fractional days to a whole number of days.

        # Example:
        # 10.2 days → 11 days
        days_to_add = math.ceil(remaining_days)

        predicted_date = (
            today + timedelta(days=days_to_add)
        )

        return predicted_date


    # Calculate Expected Delay
  

    @staticmethod
    def calculate_expected_delay(project, today=None):
        """
        Calculate how many days earlier or later
        the project is expected to finish compared
        with its deadline.

        Returns:

            Negative value:
                Expected to finish before the deadline.

            Zero:
                Expected to finish on the deadline.

            Positive value:
                Expected to finish after the deadline.

            None:
                Prediction is not available.
        """

        if today is None:
            today = date.today()

        # Get predicted completion date.
        predicted_date = Predictor.predict_completion_date(
            project,
            today
        )

        # Prediction is not available.
        if predicted_date is None:
            return None

        # Compare predicted date with project deadline.
        delay = (
            predicted_date - project.deadline
        ).days

        return delay

    # Check If Project Will Be Late


    @staticmethod
    def will_be_late(project, today=None):
        """
        Check whether the project is expected to finish
        after its deadline.

        Returns:
            True  -> expected to be late
            False -> expected to finish on time or early
            None  -> prediction is not available
        """

        delay = Predictor.calculate_expected_delay(
            project,
            today
        )

        if delay is None:
            return None

        return delay > 0

    # Get Prediction Summary
    

    @staticmethod
    def get_prediction_summary(project, today=None):
        """
        Return all prediction-related information
        in one dictionary.

        This method is useful for the UI because it can
        get all prediction values with one function call.

        Returned dictionary:

            {
                "progress_rate": ...,
                "remaining_progress": ...,
                "remaining_days": ...,
                "predicted_date": ...,
                "expected_delay": ...,
                "will_be_late": ...
            }

        If prediction is impossible, the prediction values
        will be None.
        """

        if today is None:
            today = date.today()

        progress_rate = Predictor.calculate_progress_rate(
            project,
            today
        )

        remaining_progress = (
            Predictor.calculate_remaining_progress(project)
        )

        remaining_days = Predictor.calculate_remaining_days(
            project,
            today
        )

        predicted_date = Predictor.predict_completion_date(
            project,
            today
        )

        expected_delay = Predictor.calculate_expected_delay(
            project,
            today
        )

        late = Predictor.will_be_late(
            project,
            today
        )

        return {
            "progress_rate": progress_rate,
            "remaining_progress": remaining_progress,
            "remaining_days": remaining_days,
            "predicted_date": predicted_date,
            "expected_delay": expected_delay,
            "will_be_late": late
        }
