import json
import os
import requests
import sqlite3
from threading import Thread, Event

from corepi.actors.probes import *


class DatabaseService(Thread):
    def __init__(self, database, timer=1):
        super(DatabaseService, self).__init__()
        self.database = database
        self.data = {}
        self.sleep_minutes = timer
        self.event = Event()
        self.thresholds = {}

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

    def update_thresholds(self, probe: Probe):
        if isinstance(probe, Co2Probe):
            probe.co2_threshold = self.thresholds['co2']
            probe.temperature_threshold = self.thresholds['temperature']
            probe.humidity_threshold = self.thresholds['humidity']
        elif isinstance(probe, VocProbe):
            probe.voc_threshold = self.thresholds['voc']
        elif isinstance(probe, ParticleProbe):
            probe.pm1_threshold = self.thresholds['pm1']
            probe.pm2_threshold = self.thresholds['pm2']
            probe.pm10_threshold = self.thresholds['pm10']

    def set(self):
        self.event.set()

    def update_threshold_values(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("SELECT * FROM air_thresholds WHERE id=1;")
        row = cur.fetchall()
        if row:
            row = dict(row[0])
            row.pop('id')
            self.thresholds = row
            print("Updated threshold values")

    def update_air_values_local(self, db_conn):
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

    def update_air_values_remote(self):
        uri = os.getenv("DATABASE_WEBSITE_URI")
        if uri:
            req = requests.post(uri, data=json.dumps(self.data))
            print("Sent data to server. Status code:", req.status_code)

    def run(self) -> None:
        try:
            db_conn = sqlite3.connect(self.database)
            db_conn.row_factory = sqlite3.Row
        except Exception as e:
            print("Failed to connect to local database:", e)
            db_conn = False
        while not self.event.is_set():
            event = False
            for i in range(self.sleep_minutes * 12):
                self.update_threshold_values(db_conn)
                if self.event.wait(5):
                    break
            if self.event.is_set():
                break
            self.update_air_values_local(db_conn)
            self.update_air_values_remote()
        if db_conn:
            db_conn.close()
