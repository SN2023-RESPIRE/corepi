import json
import os
import requests
import sqlite3
from threading import Thread, Event

from corepi.actors.probes import *


class DatabaseService(Thread):
    def __init__(self, database, timer=60):
        super(DatabaseService, self).__init__()
        self.database = database
        self.send_data = False
        self.data = {}
        self.timer = timer
        self.event = Event()

    def update_values_from_probe(self, probe: Probe):
        if isinstance(probe, Co2Probe):
            self.data['co2_amount'] = probe.co2_amount
            self.data['humidity'] = probe.humidity
            self.data['temperature'] = probe.temperature
        elif isinstance(probe, VocProbe):
            self.data['voc_amount'] = probe.voc_amount
        elif isinstance(probe, ParticleProbe):
            self.data['pm1_amount'] = probe.pm1_amount
            self.data['pm2_amount'] = probe.pm2_amount
            self.data['pm10_amount'] = probe.pm10_amount

    def set(self):
        self.event.set()

    def run(self) -> None:
        try:
            db_conn = sqlite3.connect(self.database)
        except Exception as e:
            print("Failed to connect to local database:", e)
            db_conn = False
        while not self.event.is_set():
            if self.event.wait(self.timer):
                break
            req = "UPDATE air_data SET "
            for key in self.data.keys():
                req += f"{key} = {self.data[key]}, "  # Generate SQL request based on
            req = req[:-2] + " WHERE id = 1;"  # Strip away comma
            if db_conn:
                try:
                    with db_conn:  # Lock the database while writing
                        db_conn.execute(req)
                    print(req)
                except Exception as e:
                    print("Failed to update internal database:", e)
            uri = os.getenv("DATABASE_WEBSITE_URI")
            if uri:
                req = requests.post(uri, data=json.dumps(self.data))
                print("Sent data to server. Status code:", req.status_code)
        if db_conn:
            db_conn.close()
