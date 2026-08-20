import unittest
from datetime import date

import pandas as pd
from pydantic import ValidationError

from etl.transform import transform


class TestTransform(unittest.TestCase):

    def test_transform_raises_validation_error_on_bad_types(self):
        """Verify Pydantic raises error if a value can't be coerced to the schema's type."""
        
        bad_df = pd.DataFrame([
            {"id": "STA1", "date": 20200101, "element": "TMAX", "value": "NOT_A_NUMBER", "qflag": None}
        ])

        with self.assertRaises(ValidationError):
            transform(bad_df)

    def test_transform_converts_tenths_to_units(self):
        """TMAX/TMIN/PRCP arrive from GHCNd in tenths and must be divided by 10."""

        dly = pd.DataFrame([
            {"id": "STA1", "date": 20200101, "element": "TMAX", "value": 350, "qflag": None},
            {"id": "STA1", "date": 20200101, "element": "TMIN", "value": -50, "qflag": None},
            {"id": "STA1", "date": 20200101, "element": "PRCP", "value": 100, "qflag": None},
        ])

        result = transform(dly).iloc[0]

        self.assertEqual(result["TMAX"], 35.0)
        self.assertEqual(result["TMIN"], -5.0)
        self.assertEqual(result["PRCP"], 10.0)


if __name__ == "__main__":
    unittest.main()
