import serial


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
            print(bytes(data).hex(' '))


if __name__ == '__main__':
    main()
