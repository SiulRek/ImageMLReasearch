import json
import os

from src.experimenting.helpers.create_experiment_report import create_experiment_report
from src.experimenting.helpers.datetime_utils import get_datetime, get_duration
from src.experimenting.helpers.trial import Trial
from src.research.attributes.research_attributes import ResearchAttributes


class ExperimentError(Exception):
    """ Exception raised for errors that occur during the experiment. """


class Experiment(ResearchAttributes):
    """ A class to manage experiments and trials, inheriting from
    ResearchAttributes. """

    def __init__(
        self, research_attributes, directory, name, description, report_kwargs=None
    ):
        """
        Initializes the Experiment with the given parameters.

        Args:
            - research_attributes (ResearchAttributes): The research
                attributes for the experiment.
            - directory (str): The directory to save the experiment data.
            - name (str): The name of the experiment.
            - description (str): The description of the experiment.
            - report_kwargs (dict, optional): Additional keyword arguments
                for the report.

        Note:
            - `Experiment` is the only research module that requires
                `research_attributes` during initialization, as it simplifies
                the usage within a context manager.
        """
        super().__init__()

        # Initialize research attributes used in the Experiment
        self._figures = {}  # Read only
        self._evaluation_metrics = {}  # Read only

        experiment_directory = self._make_experiment_directory(directory, name)
        self.experiment_data = {
            "name": name,
            "description": description,
            "start_time": None,
            "duration": None,
            "directory": experiment_directory,
            "trials": [],
        }
        self.synchronize_research_attributes(research_attributes)
        self.report_kwargs = report_kwargs or {}

    def _make_experiment_directory(self, directory, name):
        """
        Creates the experiment directory.

        Args:
            - directory (str): The directory to save the experiment data.
            - name (str): The name of the experiment.

        Returns:
            - str: The path to the experiment directory.
        """
        experiment_dir = os.path.join(
            os.path.abspath(os.path.normpath(directory)), name.replace(" ", "_")
        )
        os.makedirs(experiment_dir, exist_ok=True)
        return experiment_dir

    def _write_experiment_data(self):
        """ Writes the experiment data to a JSON file. """
        info_json = os.path.join(
            self.experiment_data["directory"], "experiment_info.json"
        )
        experiment_data = self.experiment_data.copy()
        experiment_data.pop("trials")

        with open(info_json, "w", encoding="utf-8") as f:
            json.dump(
                experiment_data,
                f,
                indent=4,
            )

    def __enter__(self):
        """
        Sets up the experiment by creating the necessary directories and files.

        Returns:
            - self: The Experiment instance.
        """
        self.experiment_data["start_time"] = get_datetime()
        return self

    def _sort_trials(self):
        """ Sorts the trials by the accuracy in descending order. """
        if self.experiment_data["trials"] == []:
            return
        self.experiment_data["trials"].sort(
            key=lambda x: x["evaluation_metrics"]["accuracy"], reverse=True
        )

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Cleans up the experiment and saves the report.

        Args:
            - exc_type: The exception type if an exception occurred.
            - exc_value: The exception value if an exception occurred.
            - traceback: The traceback if an exception occurred.

        Raises:
            - ExperimentError: If an exception occurred during the
                experiment.
        """
        duration = get_duration(self.experiment_data["start_time"])
        self.experiment_data["duration"] = duration

        if exc_type is not None:
            exc = exc_type(exc_value).with_traceback(traceback)
            msg = "An error occurred during the experiment."
            raise ExperimentError(msg) from exc

        self._write_experiment_data()
        self._sort_trials()
        create_experiment_report(self.experiment_data, **self.report_kwargs)

    def get_results(self):
        """
        Gets the current results (figures and evaluation_metrics) recorded in
        experiment.

        Returns:
            - dict: A dictionary containing the figures and
                evaluation_metrics.
        """
        return {
            "figures": self._figures,
            "evaluation_metrics": self._evaluation_metrics,
        }

    def trial(self, name, description, hyperparameters):
        """
        Context manager to handle trials within an experiment.

        Args:
            - name (str): Name of the trial.
            - description (str): Description of the trial.
            - hyperparameters (dict): Dictionary containing the
                hyperparameters.

        Returns:
            - Trial: A Trial context manager instance.
        """
        return Trial(self, name, description, hyperparameters)
