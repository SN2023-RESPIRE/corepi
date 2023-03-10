import sqlite3

from corepi.actors.probes import *


class DatabaseService:
    def __init__(self, database):
        self.db = sqlite3.connect(database)

    def update_values_from_probe(self, probe: Probe):
        query = None
        if isinstance(probe, Co2Probe):
            query = (f"UPDATE air_data SET"
                     f"co2_amount = {probe.co2_amount}, "
                     f"humidity = {probe.humidity}, "
                     f"temperature = {probe.temperature} "
                     f"WHERE id = 1;")
        elif isinstance(probe, VocProbe):
            query = (f"UPDATE air_data SET"
                     f"cov_amount = {probe.voc_amount} "
                     f"WHERE id = 1;")
        elif isinstance(probe, ParticleProbe):
            query = (f"UPDATE air_data SET"
                     f"pm1_amount = {probe.pm1_amount}, "
                     f"pm2_5_amount = {probe.pm2_amount}, "
                     f"pm10_amount = {probe.pm10_amount} "
                     f"WHERE id = 1;")
        if query:
            with self.db:
                self.db.execute(query)
