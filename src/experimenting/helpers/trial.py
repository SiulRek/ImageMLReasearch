from contextlib import AbstractContextManager
from copy import copy
import json
import os
import warnings

from src.research.attributes.attributes_utils import copy_public_properties
from src.research.attributes.research_attributes import ResearchAttributes
from src.utils import transform_figures_to_files
from src.utils import get_datetime, get_duration


class ResultsEmptyError(ValueError):
    """ Raised when trial results are empty and the trial was never runned before. """


def normalize_trial_name(trial_name):
    """ Normalizes the trial name by converting it to lowercase and replacing spaces
    with underscores. """
    return trial_name.replace(" ", "_").lower()


class Trial(AbstractContextManager):
    """
    A context manager class to manage individual trials within an experiment.

    Attributes:
        - experiment (Experiment): The experiment instance this trial
            belongs to.
        - research_attributes (ResearchAttributes): Research attributes from
        - trial_data (dict): Dictionary to store trial data.
        - keys: 'name', 'description', 'start_time', 'directory',
        'hyperparameters', 'figures', 'evaluation_metrics',
        'training_history' (optional).
        - trial_directory (str): Directory where the trial data is saved.
        - experiment_trials (list): Reference to the list of trials in the
            experiment, used to append the trial data.
    """

    def __init__(self, experiment, name, hyperparameters):
        """
        Initializes the Trial with the given parameters.

        Args:
            - experiment (Experiment): The experiment instance this trial
                belongs to.
            - name (str): The name of the trial.
            - hyperparameters (dict): Dictionary containing the
                hyperparameters.
        """
        self._assert_required_experiment_attributes(experiment)
        self._init_research_attributes(experiment)
        self._init_trial_data(experiment, name, hyperparameters)
        self.experiment_trials = experiment.experiment_data[
            "trials"
        ]  # Keep reference to track trials in experiment.
        self.fetch_trial_results = (
            experiment.get_results
        )  # Keep reference to retrieve results from trial.
        self.logger = experiment.logger
        self._already_runned = self._check_if_already_runned()

    @property
    def already_runned(self):
        """ Returns True if the trial has already been run, False otherwise. """
        return self._already_runned

    def _assert_required_experiment_attributes(self, experiment):
        """
        Assert if the experiment object has the required attributes.

        Args:
            - experiment (Experiment): The experiment instance to check.

        Raises:
            - AttributeError: If the experiment object does not have the
                required attributes.
        """
        required_attributes = ["figures", "evaluation_metrics"]
        for attr in required_attributes:
            if not hasattr(experiment, attr):
                msg = f"Experiment object does not have {attr} attribute."
                raise AttributeError(msg)

    def _init_research_attributes(self, experiment):
        """ Initialize the research attributes from the Experiment class. """
        self.research_attributes = ResearchAttributes()
        copy_public_properties(experiment, self.research_attributes)

    def _init_trial_data(self, experiment, name, hyperparameters):
        """
        Initialize the trial data dictionary to store trial information.

        Args:
            - experiment (Experiment): The experiment instance.
            - name (str): The name of the trial.
            - hyperparameters (dict): The hyperparameters for the trial.
        """
        trial_directory = self._make_trial_directory(
            experiment.experiment_data["directory"], normalize_trial_name(name)
        )
        self.trial_data = {
            "name": name,
            "start_time": None,
            "duration": None,
            "directory": trial_directory,
            "hyperparameters": hyperparameters,
            "figures": None,
            "evaluation_metrics": None,
            "training_history": None,
        }

    def _make_trial_directory(self, experiment_directory, name):
        """
        Creates the directory path, makes the directory and returns the path.

        Args:
            - experiment_directory (str): The directory of the experiment.
            - name (str): The name of the trial.

        Returns:
            - str: The path to the trial directory.
        """
        trial_directory = os.path.join(
            experiment_directory,
            f"{name.replace(' ', '_')}".lower(),
        )
        os.makedirs(trial_directory, exist_ok=True)
        return trial_directory

    def _check_if_already_runned(self):
        trial = self.trial_data["name"]
        experiment_trials = [trial["name"] for trial in self.experiment_trials]
        return trial in experiment_trials

    def __enter__(self):
        """
        Sets up the trial by creating the necessary directories.

        Returns:
            - self: The Trial instance.
        """

        self.trial_data["start_time"] = get_datetime()
        return self

    def _raise_exception_if_any(self, exc_type, exc_value, traceback):
        # No need to log the exception as the exception logging is handled by
        # the Experiment class.
        if exc_type is not None:
            raise

    def _remove_trial(self, trial_name):
        names = [trial["name"] for trial in self.experiment_trials]
        if trial_name not in names:
            msg = f"Trial {trial_name} not found in experiment trials."
            raise ValueError(msg)
        index = names.index(trial_name)
        self.experiment_trials.pop(index)

    def _write_trial_data(self):
        """ Writes the trial data to a JSON file. """
        trial_info_json = os.path.join(self.trial_data["directory"], "trial_info.json")
        # Remove history
        trial_data = self.trial_data.copy()
        try:
            # Hyperparameters may not be JSON serializable.
            with open(trial_info_json, "w", encoding="utf-8") as f:
                json.dump(trial_data, f, indent=4)
        except TypeError:
            msg = "Hyperparameters are not JSON serializable for trial"
            msg += f"{trial_data['name']}. Saving None instead."
            warnings.warn(msg)
            self.logger.warning("Hyperparameters are not JSON serializable")
            trial_data["hyperparameters"] = None
            with open(trial_info_json, "w", encoding="utf-8") as f:
                json.dump(trial_data, f, indent=4)

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Saves the trial data and figures and creates experiment report.

        Args:
            - exc_type: The exception type if an exception occurred.
            - exc_value: The exception value if an exception occurred.
            - traceback: The traceback if an exception occurred. C
        """
        duration = get_duration(self.trial_data["start_time"])
        self.trial_data["duration"] = duration

        self._raise_exception_if_any(exc_type, exc_value, traceback)

        trial_results = self.fetch_trial_results()

        results_empty = all(value == {} for value in trial_results.values())
        trial_name = self.trial_data["name"]
        if results_empty and self.already_runned:
            msg = f"Skipping '{trial_name}'. Already run, no new\n"
            msg += "results. Keeping old results."
            warnings.warn(msg)
            self.logger.warning(f"Skipping {trial_name}")
            return

        self.logger.info(f"Finalizing trial: {trial_name}")

        if results_empty:
            msg = f"'{trial_name}' produced no results. Nothing\n"
            msg += "saved."
            warnings.warn(msg)
            self.logger.warning(f"{trial_name} produced no results")
            return
        if self.already_runned:
            msg = f"'{trial_name}' already run. Overwriting old\n"
            msg += "results."
            warnings.warn(msg)
            self.logger.warning(f"Overwriting old results for {trial_name}")
            self._remove_trial(trial_name)

        self.trial_data["figures"] = transform_figures_to_files(
            trial_results["figures"], self.trial_data["directory"]
        )
        self.trial_data["evaluation_metrics"] = copy(
            trial_results["evaluation_metrics"]
        )
        self.trial_data["training_history"] = copy(trial_results["training_history"])

        self._write_trial_data()

        self.experiment_trials.append(self.trial_data)
