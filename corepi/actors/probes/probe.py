from abc import ABC, abstractmethod


class Probe(ABC):
    sender_id: int

    def __init__(self, sender_id):
        self.sender_id = sender_id

    @abstractmethod
    def parse(self, data):
        pass


class VocProbe(Probe):
    voc_amount: int
    voc_id: int

    def parse(self, data):
        self.voc_amount = (data[0] << 8) + data[1]
        self.voc_id = data[3]


class Co2Probe(Probe):
    co2_amount: int
    temperature: float
    humidity: float

    def parse(self, data):
        self.humidity = data[0] * 0.5
        self.co2_amount = data[1] * 10
        self.temperature = data[2] * 51 / 255


class ParticleProbe(Probe):
    pm1_amount: int
    pm2_amount: int
    pm10_amount: int

    def parse(self, data):
        particles = ((data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]) >> 5
        # Using a mask makes it a little easier
        self.pm1_amount = (particles & 0b111111111000000000000000000) >> 18
        self.pm2_amount = (particles & 0b000000000111111111000000000) >> 9
        self.pm10_amount = particles & 0b000000000000000000111111111
