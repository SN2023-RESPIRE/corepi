import serial

from crc import checksum


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
    print("===================")


def main():
    # Specifying the port in the Serial constructor will automatically open it
    port = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=57600,
        stopbits=1,
        parity=serial.PARITY_NONE,
        timeout=0.1)

    while True:
        data = port.readline()
        if data != b'':
            analyze_frame_content(data)


if __name__ == '__main__':
    main()
