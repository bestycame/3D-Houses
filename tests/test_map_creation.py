import unittest
from becode3d.map_creation import Location

class TestClass(unittest.TestCase):
	def test_location(self):
	    instance = Location("Pont Roi Baudoin Charleroi", boundary=4)
	    instance.find_files()
	    instance.create_chm()
	    html_map = instance.create_plotly_map()
	    self.assertIsInstance(instance, Location)
	    self.assertEqual(instance.boundary, 4)
	    self.assertEqual(instance.x, 154997.0999016408)
	    self.assertEqual(instance.y, 121675.1578828115)