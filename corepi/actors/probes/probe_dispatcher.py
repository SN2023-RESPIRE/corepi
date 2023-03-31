from typing import Optional

from corepi.actors.probes import Probe


class ProbeDispatcher:
    _probes: list[Probe] = []

    def register_probe(self, probe: Probe) -> None:
        self._probes.append(probe)

    def get_probe(self, sender_id: int) -> Optional[Probe]:
        for probe in self._probes:
            if probe.sender_id == sender_id:
                return probe
        return None
