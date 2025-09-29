from enum import auto
from helper_class import upperStrEnum

import unittest



class TestUpperStrEnum(unittest.TestCase):
    def test_direct_init(self):
        with self.assertRaises(TypeError) as ar:
            test_class = upperStrEnum()
            
if __name__ == "__main__":
    unittest.main()