import os
import requests
import serial
import sqlite3

from dotenv import load_dotenv

from util.crc import crc8


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


def analyze_frame_content(data: bytes) -> dict:
    # Check frame length
    length = len(data)
    if length <= 5:
        print("Invalid frame size")
        return {}

    # Check sync byte
    sync_byte = data[0]
    if sync_byte != 0x55:
        print(f"Incorrect sync byte! Expected 0x55, got {hex(sync_byte)}")
        return {}

    # Retrieve header
    data_length = data[1] * 255 + data[2]
    optional_length = data[3]
    packet_type = data[4]
    frame_header_crc = data[5]

    # Calculate checksum using whole header, excluding sync byte and CRC
    self_header_crc = crc8(data[1:5])

    # Abort on wrong checksum
    if frame_header_crc != self_header_crc:
        print(f"Invalid header CRC. Expected {hex(frame_header_crc)}, got {hex(self_header_crc)}")
        return {}

    # Retrieve data
    frame_data = 0
    optional_data = 0
    if data_length > 0:
        frame_data = data[6:6+data_length]
    if optional_length > 0:
        optional_data = data[6+data_length:6+data_length+optional_length]
    frame_data_crc = data[-1]

    # Calculate checksum using the whole frame excluding the header and data CRC
    self_data_crc = crc8(data[6:-1])

    if frame_data_crc != self_data_crc:
        print(f"Invalid data CRC. Expected {hex(frame_data_crc)}, got {hex(self_data_crc)}")
        return {}

    device_type = frame_data[0]
    sender_bytes = frame_data[-5:-1]
    sender = (sender_bytes[0] << 24) + (sender_bytes[1] << 16) + (sender_bytes[2] << 8) + sender_bytes[3]
    res = {}
    if device_type == 0xa5:
        res = analyze_4bs_data(frame_data[1:5], sender)
    return res


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

    # Specifying the port in the Serial constructor will automatically open it
    port = serial.Serial(
        port='/dev/ttyAMA0',
        baudrate=57600,
        stopbits=1,
        parity=serial.PARITY_NONE,
        timeout=0.1)

    # Receiving particle values will determine if we send data to both databases or not.
    # The first particle values obtained are ignored just to make sure we get all the values at least once.
    data_cache = {}
    ignored_first_send_request = False

    while True:
        if 21 <= port.in_waiting <= 25:
            frame = port.readall()
            data = analyze_frame_content(frame)
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
