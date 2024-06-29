from src.data_handling.labelling.label_manager import LabelManager
from src.research.attributes.attributes_utils import copy_public_properties


class ResearchAttributes:
    """
    A class to store attributes shared between modules in the research package.

    Attributes:
        - datasets_container (dict): Dictionary containing datasets. When
            creating new 'complete_dataset' is added, when split
            'train_dataset', 'val_dataset', and 'test_dataset' are added.
        - label_manager (LabelManager): LabelManager instance for handling
            labels.
        - outputs_container (dict): Dictionary containing outputs in form of
            Tuple -> (y_true, y_pred). When fitting, outputs are added. The name
            corresponds to the dataset name replacing 'dataset' with 'outputs',
            e.g. 'train_dataset' -> 'train_outputs'.
        - model (tf.keras.Model): The Keras model instance.
        - training_history (tf.keras.callbacks.History): The tracked
            training history of the model after fitting.
        - evaluation_metrics (dict): The tracked evaluation metrics dicts of
            the model after evaluating. Can be set from outside.
        - figures (dict): Dictionary containing the tracked figures.
        - {figure_name: figure}. Can be set from outside.
    """

    def __init__(self, label_type, class_names=None):
        """
        Initializes the ResearchAttributes with optional label type and class
        names.

        Args:
            - label_type (str): The type of labels used: 'binary',
                'multi_class', 'multi_label', 'multi_label_multi_class',
                'object_detection'.
            - class_names (list, optional): The list of class names.
        """
        self._datasets_container = {}
        self._label_manager = LabelManager(label_type, class_names)
        self._outputs_container = {}
        self._model = None
        self._training_history = None
        self._evaluation_metrics = None
        self._figures = {}

    @property
    def datasets_container(self):
        """ Dictionary containing datasets of type tf.data.Dataset, where each
        sample is a tuple (image, label). """
        return self._datasets_container

    @property
    def label_manager(self):
        """ LabelManager instance for handling labels. """
        return self._label_manager

    @property
    def outputs_container(self):
        """ Dictionary containing outputs in form of Tuple -> (y_true, y_pred). """
        return self._outputs_container

    @property
    def model(self):
        """ The Keras model instance. """
        return self._model

    @property
    def training_history(self):
        """ The training history of the model after fitting. """
        return self._training_history

    @property
    def evaluation_metrics(self):
        """ The evaluation metrics dicts of the model after evaluating. """
        return self._evaluation_metrics

    @evaluation_metrics.setter
    def evaluation_metrics(self, evaluation_metrics):
        """ Setter for the evaluation metrics. """
        self._evaluation_metrics = evaluation_metrics

    @property
    def figures(self):
        """ Dictionary containing figures. {figure_name: figure} """
        return self._figures

    @figures.setter
    def figures(self, figures):
        """ Setter for the figures. """
        self._figures = figures

    def update_research_attributes(self, research_attributes):
        """
        Updates the attributes of the instance with the attributes of the
        ResearchAttributes instance.

        Args:
            - instance: The class instance to insert attributes into.
        """
        if not isinstance(research_attributes, ResearchAttributes):
            msg = "The input instance must be of type ResearchAttributes."
            raise ValueError(msg)
        copy_public_properties(self, research_attributes)
