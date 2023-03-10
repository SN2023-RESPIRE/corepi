import os
import requests
import sqlite3

from dotenv import load_dotenv

from corepi.actors import FrameInterceptor
from corepi.actors.probes import *

off_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x70\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\xa2'
on_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x50\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\x5c'


def upload_data(conn: sqlite3.Connection, data: dict):
    req = "UPDATE air_data SET "
    for key in data.keys():
        req += f"{key} = {data[key]}, "  # Generate SQL request based on
    req = req[:-2] + " WHERE id = 1;"  # Strip away comma
    with conn:  # Lock the database while writing
        conn.execute(req)
    print(req)
    req = requests.post(os.getenv("DATABASE_WEBSITE_URL", "http://localhost:8000/deposit-air-data"), data)
    print('Got status code:', req.status_code)


def main():
    # load_dotenv()
    # # Connect to the SQLite database
    # conn = None
    # try:
    #     conn = sqlite3.connect("../respire.db")  # TODO: use absolute path
    #     print("Connected to local database")
    # except Exception as e:
    #     print("Failed to connect to local database.", e, sep='\n')
    #     return
    interceptor = FrameInterceptor(port='/dev/ttyUSB0')
    dispatcher = ProbeDispatcher()
    dispatcher.register_probe(Co2Probe(0xffd5a80a))
    dispatcher.register_probe(VocProbe(0xffd5a80f))
    dispatcher.register_probe(ParticleProbe(0xffd5a814))

    while True:
        if interceptor.available_frame():
            frame = interceptor.capture()
            if not frame:
                continue
            print(f"Captured frame of type {hex(frame.device_type)}")
            if frame.device_type != 0xa5:
                continue
            probe = dispatcher.get_probe(frame.sender)
            if not probe:
                continue
            probe.parse(frame.data)
            print(probe.__dict__)


if __name__ == '__main__':
    main()
