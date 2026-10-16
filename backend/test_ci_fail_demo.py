import unittest


class CiFailDemo(unittest.TestCase):
    def test_intentional_failure(self):
        self.assertEqual(1, 2)