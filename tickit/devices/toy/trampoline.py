from dataclasses import dataclass
from random import randint

from tickit.core.device import DeviceConfig, UpdateEvent
from tickit.core.typedefs import SimTime, State
from tickit.utils.compat.typing_compat import TypedDict


@dataclass
class TrampolineConfig(DeviceConfig):
    device_class = "tickit.devices.toy.trampoline.Trampoline"
    callback_period: int = int(1e9)


class Trampoline:
    def __init__(self, config: TrampolineConfig) -> None:
        self.callback_period = SimTime(config.callback_period)

    def update(self, time: SimTime, inputs: State) -> UpdateEvent:
        print("Boing! ({}, {})".format(time, inputs))
        return UpdateEvent(State(dict()), self.callback_period)


@dataclass
class RandomTrampolineConfig(DeviceConfig):
    device_class = "tickit.devices.toy.trampoline.RandomTrampoline"
    callback_period: int = int(1e9)


class RandomTrampoline:
    Output = TypedDict("Output", {"output": int})

    def __init__(self, config: RandomTrampolineConfig) -> None:
        self.callback_period = SimTime(config.callback_period)

    def update(self, time: SimTime, inputs: State) -> UpdateEvent:
        output = randint(0, 255)
        print("Boing! (delta: {}, inputs: {}, output: {})".format(time, inputs, output))
        return UpdateEvent(RandomTrampoline.Output(output=0), self.callback_period)
