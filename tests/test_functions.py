from becode3d.functions import lambert_to_wgs, wgs_to_lambert, search_address_mapbox, ErrorRaised
from os import environ
import unittest
  
class TestClass(unittest.TestCase):

	def test_lambert_to_wgs(self):
		x, y = lambert_to_wgs(182920, 106200)
		x, y = round(x, 5), round(y, 5)
		assert x, y == (50.265919, 4.830479)


	def test_wgs_to_lambert(self):
		x, y = wgs_to_lambert(50.265919, 4.830479)
		x, y = round(x, 5), round(y, 5)
		assert x, y == (182920, 106200)


	def test_search_address_mapbox_results_as_tuple_L72(self):
		address = "1 Rue de Crehen Hannut"
		result = search_address_mapbox(address, boundary=10)
		self.assertIsInstance(result, tuple)
		self.assertEqual(7, len(result))
		self.assertIsInstance(result[-1], dict)
		for v in result[:-1]:
			self.assertIsInstance(v, float)


	def test_search_address_mapbox_results_as_tuple_WGS(self):
		address = "1 Rue de Crehen Hannut"
		result = search_address_mapbox(address, as_dict=True, as_wgs=True)
		self.assertIsInstance(result, dict)
		self.assertIsInstance(result['address'], dict)
		result.pop('address', None)
		for k in result.keys():
			self.assertIsInstance(result[k], float)

	def test_search_address_mapbox_results_none(self):
		with self.assertRaises(ErrorRaised):
			search_address_mapbox("ThisIsAnIncorrectAdress")

if __name__ == '__main__':
	unittest.main()
