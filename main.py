import os
import requests
import sqlite3

from dotenv import load_dotenv

from enocean.actors import FrameInterceptor


off_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x70\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\xa2'
on_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x50\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\x5c'


def analyze_4bs_data(data: bytes, sender: int) -> dict:
    if sender == 0xffd5a80a:  # CO2 + Temperature + Humidity sensor
        print("CO2 + Temperature + Humidity sensor frame")
        humidity = data[0] * 0.5
        co2 = data[1] * 10
        temp = data[2] * 51 / 255
        return {
            "humidity": humidity,
            "co2_amount": co2,
            "temperature": temp,
        }
    elif sender == 0xffd5a80f:  # VOC sensor
        print("VOC sensor frame")
        voc_amount = (data[0] << 8) + data[1]
        voc_id = data[3]
        return {
            "cov_amount": voc_amount,
        }
    elif sender == 0xffd5a814:  # Particles sensor
        print("Particle sensor frame")
        particles = ((data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]) >> 5
        # Using a mask makes it a little easier
        pm1 = (particles & 0b111111111000000000000000000) >> 18
        pm2 = (particles & 0b000000000111111111000000000) >> 9
        pm10 = particles & 0b000000000000000000111111111
        return {
            "pm1_amount": pm1,
            "pm2_5_amount": pm2,
            "pm10_amount": pm10,
            "send_data": True  # Because of a bigger frame interval, this will determine whether data should be sent
        }
    else:
        print("Unidentified 4BS device detected")
        return {}


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
    load_dotenv()
    # Connect to the SQLite database
    conn = None
    try:
        conn = sqlite3.connect("../respire.db")  # TODO: use absolute path
        print("Connected to local database")
    except Exception as e:
        print("Failed to connect to local database.", e, sep='\n')
        return

    interceptor = FrameInterceptor(port='/dev/ttyUSB0')

    # Receiving particle values will determine if we send data to both databases or not.
    # The first particle values obtained are ignored just to make sure we get all the values at least once.
    data_cache = {}
    ignored_first_send_request = False

    while True:
        if interceptor.available_frame():
            frame = interceptor.capture()
            if not frame:
                continue
            print(f"Captured frame of type {hex(frame.device_type)}")
            if frame.device_type != 0xa5:
                continue
            data = analyze_4bs_data(frame.data, frame.sender)
            for k, d in data.items():
                if k == "send_data":
                    continue
                data_cache[k] = d
            if data.get("send_data") is not None:
                if ignored_first_send_request:
                    upload_data(conn, data_cache)
                else:
                    ignored_first_send_request = True


if __name__ == '__main__':
    main()
