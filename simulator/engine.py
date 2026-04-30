from __future__ import annotations

from typing import List

from models.state import TankSample


def run_simulation(steps: int = 60) -> List[TankSample]:
    samples: List[TankSample] = []

    for t in range(steps):
        base_level = max(0.22, 0.88 - (t * 0.003))
        leak_rate = 0.0
        vibration = 0.12
        valve_open = False
        camera_obstruction = 0.02

        if 20 <= t < 30:
            vibration = 0.32
        if 30 <= t < 45:
            valve_open = True
            leak_rate = 0.015 + ((t - 30) * 0.003)
            base_level -= (t - 29) * 0.006
        if t >= 45:
            valve_open = True
            leak_rate = 0.06
            base_level -= 0.11
            camera_obstruction = 0.08

        level = max(0.05, min(1.0, base_level))
        pressure = 1.12 - leak_rate * 2.4 + (0.03 if valve_open else 0.0)
        flow_rate = 0.35 + leak_rate * 9.5
        temperature = 25.0 + (0.4 if valve_open else 0.0)

        samples.append(
            TankSample(
                t=t,
                level=round(level, 3),
                pressure=round(pressure, 3),
                flow_rate=round(flow_rate, 3),
                temperature=round(temperature, 2),
                leak_rate=round(leak_rate, 3),
                vibration=round(vibration, 3),
                valve_open=valve_open,
                camera_obstruction=round(camera_obstruction, 3),
            )
        )

    return samples
