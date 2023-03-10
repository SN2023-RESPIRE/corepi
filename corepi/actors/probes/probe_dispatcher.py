from typing import Optional

from corepi.actors.probes import Probe


class ProbeDispatcher:
    _probes = []

    @staticmethod
    def register_probe(probe: Probe) -> None:
        ProbeDispatcher._probes.append(probe)

    @staticmethod
    def get_probe(sender_id: int) -> Optional[Probe]:
        for probe in ProbeDispatcher._probes:
            if probe.sender_id == sender_id:
                return probe
        return None
