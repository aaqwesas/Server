import unittest

from helper_class import RequestType


class TestRequestType(unittest.TestCase):
    def test_RequestType(self):
        self.assertEqual(RequestType.DELETE, "DELETE")
        self.assertEqual(RequestType.GET, "GET")
        self.assertEqual(RequestType.PATCH, "PATCH")
        self.assertEqual(RequestType.POST, "POST")
        self.assertEqual(RequestType.PUT, "PUT")

if __name__ == "__main__":
    unittest.main()
# @description 

