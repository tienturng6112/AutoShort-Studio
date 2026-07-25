import os
import tempfile
import unittest

class BaseAcceptanceTest(unittest.TestCase):
    """Base class for pipeline verification and end-to-end acceptance scenarios."""
    
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = self._temp_dir.name
        
    def tearDown(self) -> None:
        self._temp_dir.cleanup()
