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
    visual_score = round((selected_t / max(1, len(samples) - 1)) * 100)
    scene_state = {
        "t": current.t,
        "level": current.level,
        "pressure": current.pressure,
        "flow_rate": current.flow_rate,
        "leak_rate": current.leak_rate if (current.leak_rate > 0 or auto_leak) else 0.0,
        "temperature": current.temperature,
        "vibration": current.vibration,
        "valve_open": current.valve_open,
        "visual_score": visual_score,
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
        .hud { position: absolute; top: 16px; left: 16px; color: #dbeafe; background: rgba(15,23,42,.82); padding: 12px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; min-width: 260px; box-shadow: 0 12px 28px rgba(0,0,0,.35); }
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
        scene.fog = new THREE.Fog(0x0b1220, 18, 42);

        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 560, 0.1, 1000);
        camera.position.set(0, 8, 20);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, 560);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambient);
        const dir = new THREE.DirectionalLight(0xffffff, 1.2);
        dir.position.set(10, 20, 10);
        dir.castShadow = true;
        dir.shadow.mapSize.width = 2048;
        dir.shadow.mapSize.height = 2048;
        scene.add(dir);
        const accent = new THREE.PointLight(0x4488ff, 0.6);
        accent.position.set(-5, 5, -5);
        scene.add(accent);

        const floor = new THREE.Mesh(
          new THREE.PlaneGeometry(34, 34),
          new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.95 })
        );
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        scene.add(floor);

        const mainTankMaterial = new THREE.MeshStandardMaterial({ color: 0x8a9bb0, metalness: 0.7, roughness: 0.3 });
        const residueTankMaterial = new THREE.MeshStandardMaterial({ color: 0x2d4a2d, metalness: 0.5, roughness: 0.5 });
        const darkMetal = new THREE.MeshStandardMaterial({ color: 0x1a1a2e, metalness: 0.8, roughness: 0.2 });
        const pipeMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.55, roughness: 0.28 });

        const tankGroup = new THREE.Group();
        tankGroup.position.y = 3.2;
        scene.add(tankGroup);

        const mainTankBody = new THREE.Mesh(
          new THREE.CylinderGeometry(2.2, 2.2, 10.5, 64, 1, true),
          mainTankMaterial
        );
        mainTankBody.rotation.z = Math.PI / 2;
        mainTankBody.castShadow = true;
        mainTankBody.receiveShadow = true;
        tankGroup.add(mainTankBody);

        const capLeft = new THREE.Mesh(new THREESphereGeometry(2.2, 32, 32, 0, Math.PI), mainTankMaterial);
        capLeft.rotation.z = Math.PI / 2;
        capLeft.position.x = -5.25;
        capLeft.castShadow = true;
        capLeft.receiveShadow = true;
        tankGroup.add(capLeft);

        const capRight = new THREE.Mesh(new THREESphereGeometry(2.2, 32, 32, 0, Math.PI), mainTankMaterial);
        capRight.rotation.z = -Math.PI / 2;
        capRight.position.x = 5.25;
        capRight.castShadow = true;
        capRight.receiveShadow = true;
        tankGroup.add(capRight);

        const tankEdges = new THREE.LineSegments(
          new THREE.EdgesGeometry(new THREE.CylinderGeometry(2.2, 2.2, 10.5, 24, 1, true)),
          new THREE.LineBasicMaterial({ color: 0xb8c4d6, transparent: true, opacity: 0.45 })
        );
        tankEdges.rotation.z = Math.PI / 2;
        tankGroup.add(tankEdges);

        [-3.2, 0, 3.2].forEach((x) => {
          const band = new THREE.Mesh(
            new THREE.TorusGeometry(2.24, 0.05, 12, 48),
            new THREE.MeshStandardMaterial({ color: 0xc7d1dd, metalness: 0.75, roughness: 0.22 })
          );
          band.rotation.y = Math.PI / 2;
          band.position.x = x;
          band.castShadow = true;
          tankGroup.add(band);
        });

        [-3.6, 3.6].forEach((x) => {
          const legLeft = new THREE.Mesh(new THREE.BoxGeometry(0.35, 2.1, 0.35), pipeMat);
          legLeft.position.set(x, -2.2, -1.1);
          legLeft.castShadow = true;
          legLeft.receiveShadow = true;
          tankGroup.add(legLeft);
          const legRight = legLeft.clone();
          legRight.position.z = 1.1;
          tankGroup.add(legRight);

          const support = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.28, 2.8), pipeMat);
          support.position.set(x, -1.15, 0);
          support.castShadow = true;
          support.receiveShadow = true;
          tankGroup.add(support);
        });

        const fluidHeight = Math.max(0.25, state.level * 3.9);
        const liquid = new THREE.Mesh(
          new THREE.CylinderGeometry(2.0, 2.0, fluidHeight, 48),
          new THREE.MeshStandardMaterial({ color: 0x2563eb, transparent: true, opacity: 0.55, metalness: 0.15, roughness: 0.22 })
        );
        liquid.rotation.z = Math.PI / 2;
        liquid.position.set(0, -0.15, 0);
        liquid.scale.x = state.level;
        liquid.castShadow = false;
        tankGroup.add(liquid);

        const residueTank = new THREE.Mesh(
          new THREE.CylinderGeometry(0.72, 0.72, 4.2, 48),
          residueTankMaterial
        );
        residueTank.rotation.z = Math.PI / 2;
        residueTank.position.set(0.8, 0.2, 0);
        residueTank.castShadow = true;
        residueTank.receiveShadow = true;
        tankGroup.add(residueTank);

        const residueCapL = new THREE.Mesh(new THREE.SphereGeometry(0.72, 24, 24), residueTankMaterial);
        residueCapL.position.set(-1.3, 0.2, 0);
        residueCapL.scale.x = 0.55;
        residueCapL.castShadow = true;
        tankGroup.add(residueCapL);
        const residueCapR = residueCapL.clone();
        residueCapR.position.x = 2.9;
        tankGroup.add(residueCapR);

        const residueSupport = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.18, 1.0), pipeMat);
        residueSupport.position.set(0.8, -0.75, 0);
        residueSupport.castShadow = true;
        tankGroup.add(residueSupport);

        const leftValvePipe = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.0, 24), pipeMat);
        leftValvePipe.rotation.z = Math.PI / 2;
        leftValvePipe.position.set(4.6, -0.4, -1.0);
        leftValvePipe.castShadow = true;
        tankGroup.add(leftValvePipe);

        const rightValvePipe = leftValvePipe.clone();
        rightValvePipe.position.set(4.6, -0.4, 1.0);
        tankGroup.add(rightValvePipe);

        const valveColor = state.valve_open ? 0xef4444 : 0x22c55e;
        [ -1.0, 1.0 ].forEach((z) => {
          const valve = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), new THREE.MeshStandardMaterial({ color: valveColor, metalness: 0.4, roughness: 0.3 }));
          valve.position.set(5.65, -0.4, z);
          valve.castShadow = true;
          tankGroup.add(valve);
        });

        const sensor = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 0.52), new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.4, roughness: 0.35 }));
        sensor.position.set(0, 2.85, 0);
        sensor.castShadow = true;
        tankGroup.add(sensor);

        const conduitMaterial = new THREE.MeshStandardMaterial({ color: 0x597089, metalness: 0.45, roughness: 0.25 });
        const leakOrigin = new THREE.Vector3(2.9, 0.2, 0);
        const leftConduit = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 5.2, 16), conduitMaterial);
        leftConduit.position.set(-1.8, 0.85, 2.4);
        leftConduit.rotation.z = 1.18;
        leftConduit.castShadow = true;
        tankGroup.add(leftConduit);
        const rightConduit = leftConduit.clone();
        rightConduit.position.set(-1.8, 0.85, -2.4);
        rightConduit.rotation.z = -1.18;
        tankGroup.add(rightConduit);

        function ledColor(score) {
          if (score >= 90) return 0xff0000;
          if (score >= 70) return 0xffaa00;
          return 0x00ff00;
        }

        function buildCameraUnit(zPos) {
          const unit = new THREE.Group();
          unit.position.set(-2.7, 1.0, zPos);
          tankGroup.add(unit);

          const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.5, 16), darkMetal);
          arm.rotation.z = Math.PI / 3;
          arm.position.set(0.55, 0.45, 0);
          arm.castShadow = true;
          unit.add(arm);

          const body = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.46, 0.46), darkMetal);
          body.position.set(-0.1, 0.82, 0);
          body.castShadow = true;
          body.receiveShadow = true;
          unit.add(body);

          const hood = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 0.22, 24), darkMetal);
          hood.rotation.z = Math.PI / 2;
          hood.position.set(-0.48, 0.82, 0);
          hood.castShadow = true;
          unit.add(hood);

          const lens = new THREE.Mesh(
            new THREE.CircleGeometry(0.14, 24),
            new THREE.MeshStandardMaterial({ color: 0x05070d, metalness: 0.95, roughness: 0.08, transparent: true, opacity: 0.8 })
          );
          lens.rotation.y = Math.PI / 2;
          lens.position.set(-0.6, 0.82, 0);
          unit.add(lens);

          const led = new THREE.Mesh(
            new THREE.SphereGeometry(0.06, 16, 16),
            new THREE.MeshStandardMaterial({ color: ledColor(state.visual_score), emissive: ledColor(state.visual_score), emissiveIntensity: state.visual_score >= 90 ? 1.8 : 1.0 })
          );
          led.position.set(0.18, 0.95, 0.16);
          unit.add(led);
          return { unit, led };
        }

        const camLeft = buildCameraUnit(2.4);
        const camRight = buildCameraUnit(-2.4);

        const leakRate = Math.max(0, state.leak_rate);
        const leakGroup = new THREE.Group();
        leakGroup.position.copy(leakOrigin);
        tankGroup.add(leakGroup);

        if (leakRate > 0) {
          const leakPipe = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.08, 0.8, 16),
            new THREE.MeshStandardMaterial({ color: 0x4f6b4f, metalness: 0.35, roughness: 0.45 })
          );
          leakPipe.rotation.z = Math.PI / 2;
          leakPipe.position.x = 0.38;
          leakGroup.add(leakPipe);

          const puddle = new THREE.Mesh(
            new THREE.CircleGeometry(0.45 + leakRate * 9, 32),
            new THREE.MeshStandardMaterial({ color: 0x4a9e4a, transparent: true, opacity: Math.min(0.85, 0.25 + leakRate * 8) })
          );
          puddle.rotation.x = -Math.PI / 2;
          puddle.position.set(0.95, -3.17, 0);
          puddle.receiveShadow = true;
          leakGroup.add(puddle);
        }

        const particleCount = state.visual_score >= 90 ? Math.max(18, Math.floor(state.visual_score * 1.2)) : 0;
        let particleSystem = null;
        let particleMeta = [];
        if (particleCount > 0) {
          const positions = new Float32Array(particleCount * 3);
          const geometry = new THREE.BufferGeometry();
          for (let i = 0; i < particleCount; i += 1) {
            positions[i * 3] = Math.random() * 0.12;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 0.08;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 0.08;
            particleMeta.push({
              x: Math.random() * 0.12,
              y: (Math.random() - 0.5) * 0.08,
              z: (Math.random() - 0.5) * 0.08,
              vx: 0.015 + Math.random() * 0.02,
              vy: -0.02 - Math.random() * 0.03,
              vz: (Math.random() - 0.5) * 0.01
            });
          }
          geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const material = new THREE.PointsMaterial({ color: 0x4a9e4a, size: 0.08, transparent: true, opacity: Math.min(0.95, 0.35 + particleCount / 180) });
          particleSystem = new THREE.Points(geometry, material);
          particleSystem.position.copy(leakOrigin);
          tankGroup.add(particleSystem);
        }

        const responseColor = state.leak_rate >= 0.05 ? '#ef4444' : state.leak_rate > 0 ? '#f59e0b' : '#22c55e';
        document.getElementById('status').style.background = responseColor;
        document.getElementById('status').innerText = state.leak_rate >= 0.05
          ? 'Respuesta activa: aislar válvula y registrar incidente'
          : state.leak_rate > 0
          ? 'Alerta temprana: revisar fuga y bajar operación'
          : 'Monitoreo activo';

        document.getElementById('hud').innerHTML = `
          <strong>Estado del sistema</strong><br>
          t = ${state.t}<br>
          score visual = ${state.visual_score}/100<br>
          nivel = ${(state.level * 100).toFixed(1)}%<br>
          presión = ${state.pressure.toFixed(2)} bar<br>
          flujo = ${state.flow_rate.toFixed(2)}<br>
          fuga estimada = ${state.leak_rate.toFixed(3)}<br>
          válvula = ${state.valve_open ? 'abierta' : 'cerrada'}<br>
          anomalías = ${state.anomalies.length}<br>
          alertas = ${state.alerts.length}
        `;

        const blinkPhase = { value: 0 };
        function animate() {
          requestAnimationFrame(animate);
          blinkPhase.value += 0.08;
          tankGroup.rotation.y += 0.002;
          liquid.material.opacity = 0.48 + Math.sin(blinkPhase.value * 0.5) * 0.03;

          if (state.visual_score >= 90) {
            const intensity = (Math.sin(blinkPhase.value * 4) + 1) / 2;
            camLeft.led.material.emissiveIntensity = 0.5 + intensity * 2.3;
            camRight.led.material.emissiveIntensity = 0.5 + intensity * 2.3;
          }

          if (particleSystem) {
            const positions = particleSystem.geometry.attributes.position.array;
            for (let i = 0; i < particleMeta.length; i += 1) {
              const p = particleMeta[i];
              p.x += p.vx;
              p.y += p.vy;
              p.z += p.vz;
              p.vy -= 0.0018;
              if (p.y < -3.0) {
                p.x = Math.random() * 0.12;
                p.y = (Math.random() - 0.5) * 0.08;
                p.z = (Math.random() - 0.5) * 0.08;
                p.vx = 0.015 + Math.random() * 0.02;
                p.vy = -0.02 - Math.random() * 0.03;
                p.vz = (Math.random() - 0.5) * 0.01;
              }
              positions[i * 3] = p.x;
              positions[i * 3 + 1] = p.y;
              positions[i * 3 + 2] = p.z;
            }
            particleSystem.geometry.attributes.position.needsUpdate = true;
          }

          renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
          camera.aspect = container.clientWidth / 560;
          camera.updateProjectionMatrix();
          renderer.setSize(container.clientWidth, 560);
        });

        function THREESphereGeometry(radius, widthSegments, heightSegments, phiStart = 0, phiLength = Math.PI * 2) {
          return new THREE.SphereGeometry(radius, widthSegments, heightSegments, phiStart, phiLength);
        }
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
