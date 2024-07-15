import unittest

import tensorflow as tf

from src.data_handling.manipulation.enhance_dataset import enhance_dataset
from src.testing.base.base_test_case import BaseTestCase


class TestEnhanceDataset(BaseTestCase):
    """ Test suite for the enhance_dataset function. """

    def setUp(self):
        super().setUp()
        self.dataset = self.load_mnist_digits_dataset(sample_num=100)

    def test_shuffling(self):
        original_first_element = next(iter(self.dataset)).numpy()
        enhanced = enhance_dataset(self.dataset, shuffle=True, random_seed=42)
        enhanced_first_element = next(iter(enhanced)).numpy()
        self.assertFalse(
            tf.reduce_all(tf.equal(original_first_element, enhanced_first_element)),
            "Shuffling did not change the order of the dataset.",
        )

    def test_batching(self):
        enhanced = enhance_dataset(self.dataset, batch_size=10)
        self.assertEqual(
            enhanced.cardinality().numpy(),
            10,
            "Batching should create 10 batches from 100 elements.",
        )

    def test_repeating(self):
        repeated = enhance_dataset(self.dataset, repeat_num=3)
        self.assertEqual(
            repeated.cardinality().numpy(),
            300,
            "Dataset should be repeated 3 times, totaling 300 elements.",
        )

    def test_caching(self):
        try:
            enhanced = enhance_dataset(self.dataset, cache=True)
            self.assertIsInstance(
                enhanced, tf.data.Dataset, "Caching failed to return a tf.data.Dataset."
            )
        except Exception as e:
            self.fail(f"Enhance dataset with caching raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
