import unittest
from datetime import date

import pandas as pd
from sqlalchemy import text

from etl.load import get_engine, upsert_daily


class TestUpsertDaily(unittest.TestCase):

    def setUp(self):
        self.engine = get_engine()  # real local Postgres from your .env
        self.table = "test_daily_actual"
        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {self.table}"))
            conn.execute(text(
                f'CREATE TABLE {self.table} (id TEXT, date DATE, "TMAX" DOUBLE PRECISION, UNIQUE(id, date))'
            ))

    def tearDown(self):
        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {self.table}"))
            conn.execute(text("DROP TABLE IF EXISTS daily_upsert"))

    def test_reloading_a_revised_value_does_not_duplicate_the_row(self):
        day1 = pd.DataFrame({"id": ["USW00094728"], "date": [date(2024, 1, 1)], "TMAX": [10.0]})
        upsert_daily(self.engine, day1, self.table)

        day2 = pd.DataFrame({"id": ["USW00094728"], "date": [date(2024, 1, 1)], "TMAX": [10.6]})
        upsert_daily(self.engine, day2, self.table)

        result = pd.read_sql(f"SELECT * FROM {self.table}", self.engine)
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
