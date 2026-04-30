from __future__ import annotations

from typing import Iterable, List

from models.state import Anomaly, TankSample


def detect_anomalies(samples: Iterable[TankSample]) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    previous: TankSample | None = None

    for sample in samples:
        if sample.leak_rate >= 0.015:
            anomalies.append(
                Anomaly(
                    t=sample.t,
                    kind="leak",
                    value=sample.leak_rate,
                    threshold=0.015,
                    detail="Fuga estimada por descenso de nivel y aumento de flujo.",
                )
            )

        if sample.pressure <= 1.0:
            anomalies.append(
                Anomaly(
                    t=sample.t,
                    kind="pressure_drop",
                    value=sample.pressure,
                    threshold=1.0,
                    detail="Caída de presión asociada a pérdida de contención.",
                )
            )

        if previous and (previous.level - sample.level) >= 0.025:
            anomalies.append(
                Anomaly(
                    t=sample.t,
                    kind="sudden_level_drop",
                    value=round(previous.level - sample.level, 3),
                    threshold=0.025,
                    detail="Descenso brusco de nivel entre muestras consecutivas.",
                )
            )

        previous = sample

    return anomalies
