from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TankSample:
    t: int
    level: float
    pressure: float
    flow_rate: float
    temperature: float
    leak_rate: float
    vibration: float
    valve_open: bool
    camera_obstruction: float


@dataclass
class Anomaly:
    t: int
    kind: str
    value: float
    threshold: float
    detail: str


@dataclass
class Alert:
    t: int
    severity: str
    message: str
