from corepi import DatabaseService
from corepi.actors import FrameInterceptor
from corepi.actors.probes import *

off_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x70\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\xa2'
on_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x50\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\x5c'


def main():
    interceptor = FrameInterceptor(port='/dev/ttyUSB0')
    dispatcher = ProbeDispatcher()
    dispatcher.register_probe(Co2Probe(0xffd5a80a))
    dispatcher.register_probe(VocProbe(0xffd5a80f))
    dispatcher.register_probe(ParticleProbe(0xffd5a814))
    database = DatabaseService('../respire.db')

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
            database.update_values_from_probe(probe)


if __name__ == '__main__':
    main()
