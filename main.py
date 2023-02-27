import serial

from crc import checksum


def analyze_rps_data(data: int, sender: int):
    if data < 0 or data > 255:
        return

    if data == 0x70:
        print("Button B0 is pressed!")
    elif data == 0x50:
        print("Button B1 is pressed!")
    else:
        print("No button pressed")


def analyze_4bs_data(data: bytes, sender: int):
    if sender == 0xffd5a80a:  # CO2 + Temperature + Humidity sensor
        print("CO2 + Temperature + Humidity sensor frame")
        humidity = data[0] * 0.5
        co2 = data[1] * 10
        temp = data[2] * 51 / 255
        print(f"Humidity: {humidity}%")
        print(f"CO2: {co2} ppm")
        print(f"Temperature: {temp}°C")
    elif sender == 0xffd5a80f:  # VOC sensor
        print("VOC sensor frame")
        voc_amount = (data[0] << 8) + data[1]
        voc_id = data[3]
        print(f"VOC amount: {voc_amount} ppb")
        print(f"VOC type: {voc_id}")
    elif sender == 0xffd5a814:  # Particles sensor
        print("Particle sensor frame")
        particles = ((data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]) >> 5
        # Using a mask is a little easier
        pm1 = (particles & 0b111111111000000000000000000) >> 18
        pm2 = (particles & 0b000000000111111111000000000) >> 9
        pm10 = particles & 0b000000000000000000111111111
        print(f"PM1 Amount: {pm1} µg/m3")
        print(f"PM2.5 Amount: {pm2} µg/m3")
        print(f"PM10 Amount: {pm10} µg/m3")
    else:
        print("Unidentified 4BS device detected")
        return


def analyze_frame_content(data: bytes):
    # Check frame length
    length = len(data)
    if length <= 5:
        print("Invalid frame size")
        return

    # Check sync byte
    sync_byte = data[0]
    if sync_byte != 0x55:
        print(f"Incorrect sync byte! Expected 0x55, got {hex(sync_byte)}")
        return

    # Retrieve header
    data_length = data[1] * 255 + data[2]
    optional_length = data[3]
    packet_type = data[4]
    frame_header_crc = data[5]

    # Calculate checksum using whole header, excluding sync byte and CRC
    self_header_crc = checksum(data[1:5])

    # Abort on wrong checksum
    if frame_header_crc != self_header_crc:
        print(f"Invalid header CRC. Expected {hex(frame_header_crc)}, got {hex(self_header_crc)}")
        return

    # Retrieve data
    frame_data = 0
    optional_data = 0
    if data_length > 0:
        frame_data = data[6:6+data_length]
    if optional_length > 0:
        optional_data = data[6+data_length:6+data_length+optional_length]
    frame_data_crc = data[-1]

    # Calculate checksum using the whole frame excluding the header and data CRC
    self_data_crc = checksum(data[6:-1])

    if frame_data_crc != self_data_crc:
        print(f"Invalid data CRC. Expected {hex(frame_data_crc)}, got {hex(self_data_crc)}")
        return

    print("Raw frame data:")
    print(f"\t{data.hex(' ')}")
    print("Decoded frame data:")
    print(f"\tData length: {data_length}\n\tOptional Data length: {optional_length}\n"
          f"\tPacket Type: {hex(packet_type)}\n\tHeader checksum: {hex(self_header_crc)}\n"
          f"\tFrame Data: {frame_data.hex(' ')}\n\tOptional Data: {optional_data.hex(' ')}\n"
          f"\tData Checksum: {hex(self_data_crc)}")
    print(f"\tSender ID: {frame_data[-5:-1].hex(' ')}\n")
    print("-------------------")

    device_type = frame_data[0]
    sender_bytes = frame_data[-5:-1]
    sender = (sender_bytes[0] << 24) + (sender_bytes[1] << 16) + (sender_bytes[2] << 8) + sender_bytes[3]
    if device_type == 0xf6:
        analyze_rps_data(frame_data[1], sender)
    elif device_type == 0xa5:
        analyze_4bs_data(frame_data[1:5], sender)
    print("===================")


def main():
    # Specifying the port in the Serial constructor will automatically open it
    port = serial.Serial(
        port='/dev/ttyS0',
        baudrate=57600,
        stopbits=1,
        parity=serial.PARITY_NONE,
        timeout=0.1)

    while True:
        data = port.readall()
        if data != b'':
            analyze_frame_content(data)


if __name__ == '__main__':
    main()
