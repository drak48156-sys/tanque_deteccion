from simulator.engine import run_simulation
from detection.rules import detect_anomalies


def test_smoke_pipeline() -> None:
    samples = run_simulation()
    anomalies = detect_anomalies(samples)
    assert len(samples) > 0
    assert len(anomalies) > 0
