from typing import Optional

import serial

from corepi import Frame
from util import crc8


class FrameInterceptor:
    """Intercepts EnOcean frames."""
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(
            port=port,
            baudrate=57600,
            timeout=0
        )

    def available_frame(self) -> bool:
        """
        Check if there is a frame ready to pick up.
        :return: True if there is a frame waiting, False otherwise
        """
        return 21 <= self.ser.in_waiting  # TODO: make this more modular

    def capture(self) -> Optional[Frame]:
        """
        Intercept a frame.
        :return: The frame's data, or None if the frame is invalid.
        """
        data = self.ser.readall()

        # Check frame length
        length = len(data)
        if length <= 5:
            return None

        # Check sync byte
        sync_byte = data[0]
        if sync_byte != 0x55:
            return None

        # Retrieve header
        data_length = (data[1] << 8) + data[2]
        optional_length = data[3]
        packet_type = data[4]
        frame_header_crc = data[5]

        # Calculate checksum using whole header, excluding sync byte and CRC
        self_header_crc = crc8(data[1:5])

        # Abort on wrong checksum
        if frame_header_crc != self_header_crc:
            return None

        # Retrieve data
        frame_data = 0
        optional_data = 0
        if data_length > 0:
            frame_data = data[6:6 + data_length]
        if optional_length > 0:
            optional_data = data[6 + data_length:6 + data_length + optional_length]
        frame_data_crc = data[-1]

        # Calculate checksum using the whole frame excluding the header and data CRC
        self_data_crc = crc8(data[6:-1])

        if frame_data_crc != self_data_crc:
            return None

        device_type = frame_data[0]
        data_bytes = None
        if device_type == 0xf6:
            data_bytes = frame_data[1]
        elif device_type == 0xa5:
            data_bytes = frame_data[1:5]
        sender_bytes = frame_data[-5:-1]
        sender = (sender_bytes[0] << 24) + (sender_bytes[1] << 16) + (sender_bytes[2] << 8) + sender_bytes[3]
        frame = Frame()
        frame.data = data_bytes
        frame.sender = sender
        frame.device_type = device_type
        return frame
