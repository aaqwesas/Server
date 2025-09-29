import unittest

from helper_class import Command

class TestCommand(unittest.TestCase):
    def setUp(self):
        """Method to prepare the test fixture. Run BEFORE the test methods."""
        pass

    def tearDown(self):
        """Method to tear down the test fixture. Run AFTER the test methods."""
        pass

    def addCleanup(self, function, *args, **kwargs):
        """Function called AFTER tearDown() to clean resources used on test."""
        pass
    
    @classmethod
    def setUpClass(cls):
        """Class method called BEFORE tests in an individual class run. """
        pass  # Probably you may not use this one. See setUp().

    @classmethod
    def tearDownClass(cls):
        """Class method called AFTER tests in an individual class run. """
        pass  # Probably you may not use this one. See tearDown().
    
    def test_command(self):
        self.assertEqual(Command.HEALTH, "health")
        self.assertEqual(Command.START, "start")
        self.assertEqual(Command.STATUS, "status")
        self.assertEqual(Command.LIST, "list")
        self.assertEqual(Command.STOP, "stop")
        

if __name__ == "__main__":
    unittest.main()