from __future__ import annotations

from typing import Iterable, List

from models.state import Alert, Anomaly


def build_alerts(anomalies: Iterable[Anomaly]) -> List[Alert]:
    alerts: List[Alert] = []

    for anomaly in anomalies:
        if anomaly.kind == "leak":
            severity = "critical" if anomaly.value >= 0.05 else "high"
            message = f"Posible fuga detectada, tasa estimada {anomaly.value:.3f}."
        elif anomaly.kind == "pressure_drop":
            severity = "high"
            message = f"Caída de presión anómala, valor {anomaly.value:.3f}."
        else:
            severity = "medium"
            message = f"Descenso brusco de nivel detectado, delta {anomaly.value:.3f}."

        alerts.append(Alert(t=anomaly.t, severity=severity, message=message))

    return alerts
