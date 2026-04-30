from __future__ import annotations

import json
from collections import Counter

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from alerts.manager import build_alerts
from detection.rules import detect_anomalies
from simulator.engine import run_simulation


st.set_page_config(page_title="Simulación 3D de fuga", layout="wide")

samples = run_simulation()
anomalies = detect_anomalies(samples)
alerts = build_alerts(anomalies)

frame = pd.DataFrame([sample.__dict__ for sample in samples])
selected_t = st.sidebar.slider("Momento de la simulación", 0, len(samples) - 1, 35)
auto_leak = st.sidebar.checkbox("Forzar fuga visual", value=False)

current = samples[selected_t]
current_anomalies = [a for a in anomalies if a.t == selected_t]
current_alerts = [a for a in alerts if a.t == selected_t]
severity_counter = Counter(alert.severity for alert in alerts)

st.title("Demo 3D, fuga de tanque con respuesta del sistema")
st.caption("Three.js embebido en Streamlit para mostrar el derrame, sensores y respuesta del sistema.")

left, right = st.columns([1.3, 1])

with left:
    scene_state = {
        "t": current.t,
        "level": current.level,
        "pressure": current.pressure,
        "flow_rate": current.flow_rate,
        "leak_rate": current.leak_rate if (current.leak_rate > 0 or auto_leak) else 0.0,
        "temperature": current.temperature,
        "vibration": current.vibration,
        "valve_open": current.valve_open,
        "alerts": [alert.__dict__ for alert in current_alerts],
        "anomalies": [anomaly.__dict__ for anomaly in current_anomalies],
    }

    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8' />
      <style>
        body { margin: 0; background: #0b1220; overflow: hidden; font-family: Arial, sans-serif; }
        #scene { width: 100%; height: 560px; }
        .hud { position: absolute; top: 16px; left: 16px; color: #dbeafe; background: rgba(15,23,42,.82); padding: 12px 14px; border-radius: 12px; font-size: 13px; line-height: 1.45; min-width: 220px; }
        .status { position: absolute; top: 16px; right: 16px; color: white; padding: 10px 12px; border-radius: 10px; font-weight: 700; background: rgba(185,28,28,.9); }
      </style>
    </head>
    <body>
      <div id='scene'></div>
      <div class='hud' id='hud'></div>
      <div class='status' id='status'>Monitoreo activo</div>
      <script type='module'>
        import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
        const state = __SCENE_STATE__;

        const container = document.getElementById('scene');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0b1220);

        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 560, 0.1, 1000);
        camera.position.set(7, 5, 10);
        camera.lookAt(0, 1.5, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, 560);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        const ambient = new THREE.AmbientLight(0xffffff, 1.5);
        scene.add(ambient);
        const dir = new THREE.DirectionalLight(0xffffff, 1.6);
        dir.position.set(5, 10, 7);
        scene.add(dir);

        const floor = new THREE.Mesh(
          new THREE.PlaneGeometry(30, 30),
          new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.95 })
        );
        floor.rotation.x = -Math.PI / 2;
        scene.add(floor);

        const tank = new THREE.Mesh(
          new THREE.CylinderGeometry(1.6, 1.6, 4.2, 48, 1, true),
          new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.45, roughness: 0.35, side: THREE.DoubleSide })
        );
        tank.position.y = 2.2;
        scene.add(tank);

        const tankCapTop = new THREE.Mesh(
          new THREE.CircleGeometry(1.6, 48),
          new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.35 })
        );
        tankCapTop.rotation.x = -Math.PI / 2;
        tankCapTop.position.y = 4.3;
        scene.add(tankCapTop);

        const tankCapBottom = tankCapTop.clone();
        tankCapBottom.position.y = 0.1;
        scene.add(tankCapBottom);

        const liquid = new THREE.Mesh(
          new THREE.CylinderGeometry(1.42, 1.42, Math.max(0.18, state.level * 3.9), 32),
          new THREE.MeshStandardMaterial({ color: 0x2563eb, transparent: true, opacity: 0.72 })
        );
        liquid.position.y = 0.2 + (Math.max(0.18, state.level * 3.9) / 2);
        scene.add(liquid);

        const pipeMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.3 });
        const sidePipe = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.2, 24), pipeMat);
        sidePipe.rotation.z = Math.PI / 2;
        sidePipe.position.set(2.3, 1.1, 0);
        scene.add(sidePipe);

        const valve = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), new THREE.MeshStandardMaterial({ color: state.valve_open ? 0xef4444 : 0x22c55e }));
        valve.position.set(3.25, 1.1, 0);
        scene.add(valve);

        const sensor = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), new THREE.MeshStandardMaterial({ color: 0xf59e0b }));
        sensor.position.set(0, 4.7, 0);
        scene.add(sensor);

        const cameraBodyMaterial = new THREE.MeshStandardMaterial({ color: 0xe2e8f0 });
        const cam1 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.32, 0.32), cameraBodyMaterial);
        cam1.position.set(-3.2, 2.8, 2.4);
        scene.add(cam1);
        const cam2 = cam1.clone();
        cam2.position.set(3.2, 2.8, 2.4);
        scene.add(cam2);

        const leakGroup = new THREE.Group();
        scene.add(leakGroup);
        const leakRate = Math.max(0, state.leak_rate);
        if (leakRate > 0) {
          const stream = new THREE.Mesh(
            new THREE.CylinderGeometry(0.06, 0.12, 1.4 + leakRate * 6, 16),
            new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.85 })
          );
          stream.position.set(1.58, 0.7, 0);
          stream.rotation.z = 0.55;
          leakGroup.add(stream);

          const puddle = new THREE.Mesh(
            new THREE.CircleGeometry(0.5 + leakRate * 10, 32),
            new THREE.MeshStandardMaterial({ color: 0x0ea5e9, transparent: true, opacity: 0.7 })
          );
          puddle.rotation.x = -Math.PI / 2;
          puddle.position.set(2.55, 0.03, 0.25);
          leakGroup.add(puddle);
        }

        const responseColor = state.leak_rate >= 0.05 ? '#ef4444' : state.leak_rate > 0 ? '#f59e0b' : '#22c55e';
        document.getElementById('status').style.background = responseColor;
        document.getElementById('status').innerText = state.leak_rate >= 0.05
          ? 'Respuesta activa: aislar válvula y registrar incidente'
          : state.leak_rate > 0
          ? 'Alerta temprana: revisar fuga y bajar operación'
          : 'Monitoreo activo';

        document.getElementById('hud').innerHTML = `
          <strong>Estado del tanque</strong><br>
          t = ${state.t}<br>
          nivel = ${(state.level * 100).toFixed(1)}%<br>
          presión = ${state.pressure.toFixed(2)} bar<br>
          flujo = ${state.flow_rate.toFixed(2)}<br>
          fuga estimada = ${state.leak_rate.toFixed(3)}<br>
          válvula = ${state.valve_open ? 'abierta' : 'cerrada'}<br>
          anomalías = ${state.anomalies.length}<br>
          alertas = ${state.alerts.length}
        `;

        function animate() {
          requestAnimationFrame(animate);
          tank.rotation.y += 0.002;
          liquid.rotation.y += 0.002;
          renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
          camera.aspect = container.clientWidth / 560;
          camera.updateProjectionMatrix();
          renderer.setSize(container.clientWidth, 560);
        });
      </script>
    </body>
    </html>
    """.replace("__SCENE_STATE__", json.dumps(scene_state))
    components.html(html, height=580)

with right:
    st.subheader("Estado del sistema")
    a, b = st.columns(2)
    a.metric("Nivel", f"{current.level * 100:.1f}%")
    b.metric("Presión", f"{current.pressure:.2f} bar")
    a.metric("Fuga estimada", f"{current.leak_rate:.3f}")
    b.metric("Flujo", f"{current.flow_rate:.2f}")

    st.subheader("Respuesta propuesta")
    if current.leak_rate >= 0.05:
        st.error("Fuga crítica: aislar línea, detener operación y guardar evidencia local para sincronizar luego.")
    elif current.leak_rate > 0:
        st.warning("Fuga incipiente: bajar operación, disparar alerta local y marcar evento para inspección.")
    else:
        st.success("Condición estable: monitoreo local y registro continuo.")

    if current_alerts:
        st.subheader("Alertas en este momento")
        for alert in current_alerts:
            st.write(f"- [{alert.severity}] {alert.message}")
    else:
        st.caption("Sin alertas activas en esta muestra.")

st.subheader("Serie temporal")
st.line_chart(frame.set_index("t")[["level", "pressure", "flow_rate", "leak_rate"]])

col1, col2, col3 = st.columns(3)
col1.metric("Muestras", len(samples))
col2.metric("Anomalías", len(anomalies))
col3.metric("Alertas críticas", severity_counter.get("critical", 0))
