"""
This module contains a suite of tests designed to validate image preprocessing
steps before their integration into an image preprocessing pipeline. Each
preprocessing step must successfully pass all the tests specified in this module
or customized tests to ensure its functionality, compatibility, and reliability
within the pipeline!

Note:
    - Test Adaptability: The module acknowledges that not all tests in
        `TestSingleStep` are universally applicable. Therefore, it accommodates
        the need for customized modifications in test cases to effectively
        challenge and validate the diversity of image preprocessing steps.
"""

import json
import os
import unittest
from unittest.mock import patch

import tensorflow as tf

from src.preprocessing.definitions.step_class_mapping import STEP_CLASS_MAPPING
from src.preprocessing.helpers.recursive_type_conversion import (
    recursive_type_conversion,
)
from src.preprocessing.helpers.step_utils import correct_image_tensor_shape
from src.preprocessing.image_preprocessor import ImagePreprocessor
from src.preprocessing.steps import Rotator as StepToTest
from src.preprocessing.steps.step_base import StepBase
from src.testing.base.base_test_case import BaseTestCase
from src.testing.helpers.image_plotter import ImagePlotter

# TODO Select Step to test here!
STEP_PARAMETERS = {"angle": 180}

ENABLE_VISUAL_INSPECTION = True
JSON_TEMPLATE_REL = os.path.join(
    r"src/preprocessing/definitions/pipeline_template.json"
)


class RGBToGrayscale(StepBase):
    arguments_datatype = {}
    name = "RGB_to_Grayscale"

    def __init__(self):
        super().__init__(locals())

    @StepBase._tensor_pyfunc_wrapper
    def process_step(self, image_tensor):
        image_grayscale_tensor = tf.image.rgb_to_grayscale(image_tensor)
        image_grayscale_tensor = correct_image_tensor_shape(image_grayscale_tensor)
        return image_grayscale_tensor


class GrayscaleToRGB(StepBase):
    arguments_datatype = {}
    name = "Grayscale_to_RGB"

    def __init__(self):
        super().__init__(locals())

    @StepBase._tensor_pyfunc_wrapper
    def process_step(self, image_tensor):
        image_tensor = tf.image.grayscale_to_rgb(image_tensor)
        image_grayscale_tensor = correct_image_tensor_shape(image_tensor)
        return image_grayscale_tensor


class TypeCaster(StepBase):
    """ A preprocessing step that casts an image tensor to a specified data type. """

    arguments_datatype = {"output_dtype": str}
    name = "Type Caster"

    def __init__(self, output_dtype="float16"):
        """
        Initializes the TypeCaster object for integration into an image
        preprocessing pipeline.

        Args:
            - output_dtype (str): The desired data type to cast the image
                tensor to. Must be an attribute in tensorflow. Default is
                'float16'.
        """
        super().__init__(locals())
        self.output_datatype = getattr(tf, output_dtype)

    @StepBase._tensor_pyfunc_wrapper
    def process_step(self, image_tensor):
        # image_tensor = tf.cast(image_tensor, self.output_datatype) Line is already going to be accomplished by the wrapper.
        return image_tensor


class TestSingleStep(BaseTestCase):
    """
    A unit test class for testing individual image preprocessing steps in to be
    integrated in the image preprocessing framework. The class focuses on
    ensuring the correct functioning of these steps, both in isolation and when
    integrated into a pipeline.

    This class covers a variety of tests, including validating the correct
    operation of the tested preprocessing step in isolation and within a
    pipeline, confirming parameter data types, ensuring step mappings are
    appropriately configured, and testing the steps' execution and output data
    types. It also includes tests for loading JSON step configurations, saving
    and reloading pipeline configurations, and visual inspection of produced
    images.
    """

    # Class Attributes (overwritten when class is dynamically loaded (eg. multiple_steps_test.py) or customized (channel_conversion_steps_test.py))
    parameters = STEP_PARAMETERS
    TestStep = StepToTest

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.json_template = os.path.join(cls.root_dir, JSON_TEMPLATE_REL)
        cls.image_dataset = cls.load_geometrical_forms_dataset()

        cls.visual_inspection = ENABLE_VISUAL_INSPECTION
        step_name_edit = cls.TestStep.name.replace(" ", "_").lower()
        cls.step_visualization_dir = os.path.join(
            cls.visualizations_dir, step_name_edit
        )

        if cls.visual_inspection:
            if not os.path.isdir(cls.step_visualization_dir):
                os.makedirs(cls.step_visualization_dir)

    def setUp(self):
        super().setUp()
        self.json_test_file = os.path.join(self.temp_dir, "test_step.json")
        with open(self.json_test_file, "a", encoding="utf-8"):
            pass
        self.test_step = self.TestStep(**self.parameters)

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.json_test_file):
            os.remove(self.json_test_file)

    def _verify_image_shapes(
        self, processed_images, original_images, color_channel_expected
    ):
        """
        Helper method to verify the image dimensions and color channels in a
        processed dataset. Compares the processed images to the original dataset
        to ensure correct height, width, and color channel transformations.
        """
        for original_image, processed_image in zip(original_images, processed_images):
            processed_data_shape = tuple(processed_image.shape[:2].as_list())
            original_data_shape = tuple(original_image.shape[:2].as_list())
            self.assertEqual(
                processed_data_shape,
                original_data_shape,
                "heights and/or widths are not equal.",
            )
            self.assertEqual(
                color_channel_expected,
                processed_image.shape[2],
                "Color channels are not equal.",
            )

    def test_arguments_datatype(self):
        """
        Test to verify that the datatype specifications for StepToTest instance
        parameters are correct. Ensures that the actual parameters match the
        expected datatypes specified in the class.
        """

        parameters = self.test_step.parameters
        init_parameters_datatype = self.TestStep.arguments_datatype

        self.assertEqual(
            parameters.keys(),
            init_parameters_datatype.keys(),
            "'init_parameters_datatype' keys does not match with 'parameters' attribute.",
        )

        for key in parameters.keys():
            param_converted = recursive_type_conversion(
                parameters[key], init_parameters_datatype[key]
            )  # When everything goes right, no conversion is done.
            self.assertEqual(
                param_converted,
                parameters[key],
                "'init_parameters_datatype' specification is incorrect.",
            )

    def test_mapping_entry_of_step(self):
        """
        Test to verify the presence and correctness of the mapping entry for the
        tested preprocessing step. Checks if the step class is correctly mapped
        and if the mapping points to the step itself.
        """
        step_name = self.test_step.name
        self.assertIn(
            step_name,
            STEP_CLASS_MAPPING.keys(),
            "No mapping is specified for the tested step.",
        )
        self.assertIs(
            STEP_CLASS_MAPPING[step_name],
            self.TestStep,
            "Mapped value of tested step is not the tested step class itself.",
        )

    def test_process_execution(self):
        """
        Verifies the execution and efficacy of the preprocessing step on an
        image dataset. This test validates that the preprocessing step: 1.
        Executes without errors on a dataset of images. 2. Alters the images in
        a way that is detectable when compared to the original images,
        suggesting successful transformation. 3. Processes images into the
        specified output datatype of the preprocessing step.

        The test involves applying the preprocessing step to an image dataset
        and comparing the processed images against the original ones. It
        confirms that the processed images have undergone transformation by
        checking for changes in content and shape.
        """
        dtype_str = self.test_step.output_datatype.name
        image_dataset = TypeCaster(dtype_str).process_step(self.image_dataset)
        processed_images = self.test_step.process_step(image_dataset)
        for _ in processed_images.take(
            1
        ):  # Consumes the dataset to force execution of the step.
            pass
        for ori_img, prc_img in zip(image_dataset, processed_images):
            equal_flag = True
            prc_img = tf.cast(prc_img, dtype=ori_img.dtype)
            if ori_img.shape != prc_img.shape:
                equal_flag = False
            elif not tf.reduce_all(tf.equal(ori_img, prc_img)).numpy():
                equal_flag = False
            self.assertFalse(equal_flag)

    def test_output_datatype(self):
        """
        This test ensures that the datatype of the images after processing is
        consistent with the datatype defined by the preprocessing step,
        maintaining data integrity. Verifies that the output datatype of the
        processed images matches the expected datatype specified in the
        preprocessing step's output datatype configuration.
        """
        processed_images = self.test_step.process_step(self.image_dataset)
        for image in processed_images:
            self.assertEqual(image.dtype, self.test_step.output_datatype)

    def test_process_rgb_images(self):
        """
        Test to ensure that RGB images are processed correctly. Verifies that
        the RGB images, after processing, have the expected color channel
        dimensions.
        """
        pipeline = [self.test_step, RGBToGrayscale()]
        preprocessor = ImagePreprocessor()
        preprocessor.set_pipe(pipeline)
        processed_images = preprocessor.process(self.image_dataset)
        self._verify_image_shapes(
            processed_images, self.image_dataset, color_channel_expected=1
        )

    def test_process_grayscaled_images(self):
        """
        Test to ensure that grayscale images are processed correctly. Checks if
        the grayscale images maintain their dimensions after processing and
        verifies the color channel transformation correctness.
        """
        pipeline = [RGBToGrayscale(), self.test_step]
        preprocessor = ImagePreprocessor()
        preprocessor.set_pipe(pipeline)
        processed_images = preprocessor.process(self.image_dataset)
        self._verify_image_shapes(
            processed_images, self.image_dataset, color_channel_expected=1
        )
        processed_images = GrayscaleToRGB().process_step(processed_images)
        self._verify_image_shapes(
            processed_images, self.image_dataset, color_channel_expected=3
        )

    def test_load_from_json(self):
        """
        This method tests the functionality of loading a preprocessing step from
        a JSON File. It verifies that the specified preprocessing step,
        StepToTest, is correctly instantiated and configured based on the
        settings provided in the JSON file. This ensures the JSON Files's
        compatibility and correctness with the pipeline instantiation process.
        """

        step_name = self.test_step.name

        with open(self.json_template, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        self.assertIn(
            step_name, json_data.keys(), "StepToTest has no entry in JSON template."
        )

        preprocessor = ImagePreprocessor()
        preprocessor.load_pipe_from_json(self.json_template)

        step_is_instance = [
            isinstance(step, self.TestStep) for step in preprocessor.pipeline
        ]
        self.assertIn(True, step_is_instance)

    def test_save_and_load_pipeline(self):
        """
        Test to ensure the functionality of saving and loading the preprocessing
        pipeline. Confirms that the pipeline configuration is correctly
        preserved across save and load operations.
        """

        mock_mapping = {"RGB_to_Grayscale": RGBToGrayscale, "Test_Step": self.TestStep}
        with patch(
            "src.preprocessing.image_preprocessor.STEP_CLASS_MAPPING", mock_mapping
        ):
            old_preprocessor = ImagePreprocessor()
            pipeline = [RGBToGrayscale(), self.test_step]
            old_preprocessor.set_pipe(pipeline)
            old_preprocessor.save_pipe_to_json(self.json_test_file)
            new_preprocessor = ImagePreprocessor()
            new_preprocessor.load_pipe_from_json(self.json_test_file)

        self.assertEqual(
            len(old_preprocessor._pipeline),
            len(new_preprocessor._pipeline),
            "Pipeline lengths are not equal.",
        )
        for old_step, new_step in zip(
            old_preprocessor._pipeline, new_preprocessor._pipeline
        ):
            self.assertEqual(old_step, new_step, "Pipeline steps are not equal.")

    def test_processed_image_visualization(self):
        """
        This method evaluates the visualization capabilities for processed
        images. It processes RGB and grayscale images through the StepToTest,
        visualizes them using PCBVisualizerforTF, and saves these visualizations
        to files. The method allows processed images to be visually inspected.
        """
        if self.visual_inspection:
            directory = self.step_visualization_dir
            plotter = ImagePlotter(show_plot=False)
            processed_rgb_dataset = self.test_step.process_step(self.image_dataset)
            plotter.plot_images(processed_rgb_dataset, "Processed RGB Images")
            figure_name = "processed_rgb_images"
            plotter.save_plot_to_file(os.path.join(directory, figure_name))
            plotter.plot_image_comparison(
                self.image_dataset, processed_rgb_dataset, 1, "RGB Images comparison"
            )
            figure_name = "rgb_images_comparison"
            plotter.save_plot_to_file(os.path.join(directory, figure_name))

            grayscaled_dataset = RGBToGrayscale().process_step(self.image_dataset)
            processed_grayscaled_dataset = self.test_step.process_step(
                grayscaled_dataset
            )
            plotter.plot_images(
                processed_grayscaled_dataset, "Processed Grayscale Images"
            )
            figure_name = "processed_grayscaled_images"
            plotter.save_plot_to_file(os.path.join(directory, figure_name))
            plotter.plot_image_comparison(
                grayscaled_dataset,
                processed_grayscaled_dataset,
                1,
                "Grayscale Images comparison",
            )
            figure_name = "grayscaled_images_comparison"
            plotter.save_plot_to_file(os.path.join(directory, figure_name))


if __name__ == "__main__":
    unittest.main()
