import json
import os
import warnings

from src.experimenting.helpers.hparams_suggester import HParamsSuggester


class _TrialsDefinitionsIterator:
    """ An iterator class for generating trial definitions. """

    def __init__(self, suggester, num_trials, prefix):
        """
        Initialize the TrialsDefinitionsIterator.

        Args:
            - suggester (HParamsSuggester): The hyperparameters suggester
                object.
            - num_trials (int): The number of trials to generate.
        """
        self.suggester = suggester
        self.num_trials = num_trials
        self.prefix = prefix
        self.trial_count = 0

    def __iter__(self):
        """
        Return the iterator object.

        Returns:
            - iterator: The iterator object.
        """
        return self

    def __next__(self):
        """
        Generate the next trial definition.

        Returns:
            - dict: The trial definition.

        Raises:
            - StopIteration: If all num_trials are already generated.
        """
        if self.trial_count == self.num_trials:
            raise StopIteration
        self.trial_count += 1
        name = f"{self.prefix}{self.trial_count}"
        hparams = self.suggester.suggest_next()
        return {"name": name, "hyperparameters": hparams}


def _load_definitions(definitions_json):
    """
    Load experiment information from a JSON file.

    Args:
        - definitions_json (str): The path to the directory containing the
            definitions.json file.

    Returns:
        - dict: A dictionary containing the experiment information.
    """
    if not os.path.exists(definitions_json):
        msg = f"{definitions_json} is not found in the experiment directory."
        raise FileNotFoundError(msg)
    with open(definitions_json, encoding="utf-8") as f:
        experiment_info = json.load(f)
    return experiment_info


def _assert_experiment_definitions(experiment_definitions):
    expected_keys = ["name", "description", "directory"]
    for key in expected_keys:
        assert (
            key in experiment_definitions
        ), f"{key} is not found in experiment_definitions."


def _process_trials_definitions(trials_definitions):
    """
    Process the trials definitions to include the trial names.

    Args:
        - trials_definitions (list or dict): The trials definitions. It can
            be a list of dicts or a dict containing the hyperparameters
            configurations to be passed to HParamsSuggester class.

    Returns:
        - iterator: An iterator of the trial definitions.
    """
    # There are 2 options to define the trials. Option 1: Set manually the
    # trials providing a list of dicts. The dict should contain trial name and
    # hyperparameters.
    if isinstance(trials_definitions, list):
        expected_keys = {"name", "hyperparameters"}
        for trial in trials_definitions:
            assert (
                set(trial.keys()) == expected_keys
            ), "Invalid keys in list elements of trials_definitions."
        return iter(trials_definitions)

    # Option 2: Set the trials automatically by providing the hyperparameters
    # configurations. The trials will be generated by the hyperparameters
    # suggester. The names of the trials are generated automatically as well.
    if isinstance(trials_definitions, dict):
        num_trials = trials_definitions.pop("num_trials", 1)  # Default 1 trial.
        prefix = trials_definitions.pop(
            "prefix", "trial_"
        )  # Default prefix is "trial_".
        hparams_configs = trials_definitions.pop("hparams_configs", None)
        assert (
            hparams_configs is not None
        ), "hparams_configs is not a key in trials_definitions."
        if trials_definitions != {}:
            for key in trials_definitions.keys():
                msg = f"Ignoring key '{key}' in trials_definitions."
                warnings.warn(msg)
        try:
            suggester = HParamsSuggester(hparams_configs)
        except AssertionError as e:
            msg = "Invalid hparams_configs in trials_definitions."
            raise AssertionError(msg) from e
        return _TrialsDefinitionsIterator(suggester, num_trials, prefix)

    msg += "trials_definitions should be a list or a dict."
    raise ValueError(msg)


def load_definitions_of_experiment(definitions_json):
    """
    Load the experiment definitions and trials definitions from a JSON file.

    Args:
        - definitions_json (str): The path to the JSON file containing the
            definitions.

    Returns:
        - tuple: A tuple containing the experiment definitions and trials
            definitions.
    """
    definitions = _load_definitions(definitions_json)
    assert len(definitions) == 2, "Expected 2 keys in the definitions file."
    assert (
        "experiment_definitions" in definitions
    ), "experiment_definitions is not found in the definitions file."
    assert (
        "trials_definitions" in definitions
    ), "trials_definitions is not found in the definitions file."
    experiment_definitions = definitions["experiment_definitions"]
    _assert_experiment_definitions(experiment_definitions)
    trials_definitions = definitions["trials_definitions"]
    trials_definitions = _process_trials_definitions(trials_definitions)
    return experiment_definitions, trials_definitions
