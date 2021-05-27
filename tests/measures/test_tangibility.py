import unittest
from frds.data.wrds.comp import funda, fundq
from frds.io.wrds import load
from frds.measures import Tangibility


class TangibilityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.FUNDA = load(funda, use_cache=True, save=False, obs=100)
        self.FUNDQ = load(fundq, use_cache=True, save=False, obs=100)

    def test_tangibility_default(self):
        Tangibility(self.FUNDA)
        Tangibility(self.FUNDQ)