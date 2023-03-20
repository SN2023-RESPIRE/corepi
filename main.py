from dotenv import load_dotenv

from corepi import DatabaseService
from corepi.actors import FrameInterceptor
from corepi.actors.probes import *

off_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x70\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\xa2'
on_frame = b'\x55\x00\x07\x07\x01\x7a\xf6\x50\xff\xfb\xd8\x80\x30\x02\xff\xff\xff\xff\x7f\x00\x5c'


def main():
    load_dotenv()

    interceptor = FrameInterceptor(port='/dev/ttyUSB0')
    dispatcher = ProbeDispatcher()
    dispatcher.register_probe(Co2Probe(0xffd5a80a))
    dispatcher.register_probe(VocProbe(0xffd5a80f))
    dispatcher.register_probe(ParticleProbe(0xffd5a814))
    database = DatabaseService('../respire.db')
    database.start()
    print("Database thread started")

    is_ventilating = False
    ventilation_data = []

    try:
        while True:
            if interceptor.available_frame():
                frame = interceptor.capture()
                if not frame:
                    continue
                if frame.device_type != 0xa5:
                    continue
                probe = dispatcher.get_probe(frame.sender)
                if not probe:
                    continue
                print(f"Captured frame from {type(probe).__name__}")
                probe.parse(frame.data)
                thresholds = database.update_thresholds(probe)
                in_list = probe.sender_id in ventilation_data
                reached_threshold = probe.reached_threshold()
                if reached_threshold and not in_list:
                    ventilation_data.append(probe.sender_id)
                elif not reached_threshold and in_list:
                    ventilation_data.remove(probe.sender_id)
                vent_len = len(ventilation_data)
                if vent_len > 0 and not is_ventilating:
                    interceptor.send_frame(on_frame)
                    is_ventilating = True
                    print("Turning fan on")
                elif vent_len == 0 and is_ventilating:
                    interceptor.send_frame(off_frame)
                    is_ventilating = False
                    print("Turning fan off")
                database.update_values_from_probe(probe)
    except KeyboardInterrupt:
        print("Stopping database service")
        database.set()


if __name__ == '__main__':
    main()
