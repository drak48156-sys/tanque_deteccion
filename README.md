# tanque_deteccion

Proyecto y repositorio para simular detección de fugas en tanques con apoyo visual 3D.

## Qué incluye
- simulación sintética del estado del tanque
- reglas simples de detección de fuga
- alertas por severidad
- demo 3D con Three.js embebida en Streamlit
- base lista para evolucionar a sensores, ruta, camión y operación offline

## Estructura
- `simulator/` genera muestras del tanque
- `detection/` detecta anomalías
- `alerts/` construye alertas
- `models/` define estructuras de datos
- `dashboard/` contiene la interfaz y escena 3D
- `tests/` pruebas mínimas

## Cómo correr
```bash
python3 main.py
```

Para la demo web:
```bash
python3 -m streamlit run dashboard/app.py
```

## Dependencias
```bash
pip install -r requirements.txt
```

## Objetivo inmediato
Mostrar de forma clara cómo se vería una fuga, qué variables del sistema cambian y cómo reaccionaría la propuesta.
