import unittest

from calculator import divide


class DivideTests(unittest.TestCase):
    def test_integer_result(self):
        self.assertEqual(divide(6, 3), 2)

    def test_fractional_result(self):
        self.assertEqual(divide(7, 2), 3.5)

    def test_zero_divisor(self):
        with self.assertRaises(ZeroDivisionError):
            divide(1, 0)


if __name__ == '__main__':
    unittest.main()
