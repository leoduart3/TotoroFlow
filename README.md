# TotoroFlow

TotoroFlow es un roster semanal para restaurantes medianos. Modela empleados, roles, disponibilidad y cobertura, y usa **Google OR-Tools CP-SAT** para encontrar asignaciones válidas.

## Ejecutar

Requiere Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000. La demo inicia con 12 empleados y cobertura de cuatro funciones. `pytest` ejecuta las pruebas del motor.

Las restricciones duras son roles, disponibilidad, cobertura, solapamientos y máximos de horas. La arquitectura mantiene el optimizador (`app/scheduler.py`) independiente de FastAPI y la presentación Jinja. El siguiente paso natural es persistir empleados y planificaciones con SQLAlchemy/SQLite, además de edición por turno.
