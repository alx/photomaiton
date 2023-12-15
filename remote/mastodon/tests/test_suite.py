# test_suite.py

import unittest

def suite():
    loader = unittest.TestLoader()
    suite = loader.discover('tests')  # discover all tests in this directory
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
