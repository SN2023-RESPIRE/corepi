import serial

from crc import checksum


def analyze_frame_content(data: bytes):
    length = len(data)
    if length <= 5:
        print("Invalid packet size")
        return
    sync_byte = data[0]
    if sync_byte != 0x55:
        print(f"Incorrect sync byte! Expected 0x55, got {hex(sync_byte)}")
        return
    data_length = data[1] * 255 + data[2]
    optional_length = data[3]
    packet_type = data[4]
    frame_header_crc = data[5]
    self_header_crc = checksum(data[1:5])  # Calculate checksum using whole header, excluding sync byte and CRC
    if frame_header_crc != self_header_crc:
        print(f"Invalid header CRC. Expected {hex(frame_header_crc)}, got {hex(self_header_crc)}")
        return

    print("Raw frame data:")
    print(f"\t{data.hex(' ')}")
    print("Decoded frame data:")
    print(f"\tData length: {data_length}\n\tOptional Data length: {optional_length}\n"
          f"\tPacket Type: 0x{packet_type:x}\n\tFrame checksum: 0x{self_header_crc:x}")
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
