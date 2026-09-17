"""TotoroFlow web application: validated CRUD around the scheduling engine."""
import re
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import AssignmentRow, Employee, OperationalNeed, SavedSchedule, init_db, session
from .scheduler import Need, Worker, generate_schedule

app = FastAPI(title="TotoroFlow")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

ROLES = ("Caja", "Cocina", "Servicio", "Bartender", "Limpieza", "Supervisor")
DAYS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ '\-]{1,59}$")
DEMO = [("Ana Torres", ["Caja"]), ("Bruno Silva", ["Caja", "Servicio"]), ("Carla Méndez", ["Cocina"]), ("Diego Rojas", ["Cocina"]), ("Elena Paz", ["Servicio"]), ("Fabián Núñez", ["Servicio", "Bartender"]), ("Gina Vera", ["Limpieza"]), ("Hugo Sosa", ["Supervisor", "Caja"]), ("Iris Benítez", ["Cocina", "Limpieza"]), ("Julián Acosta", ["Servicio"]), ("Karen Ortiz", ["Cocina"]), ("Leo Giménez", ["Limpieza", "Servicio"])]


def redirect(message: str = "", error: str = "") -> RedirectResponse:
    params = {key: value for key, value in {"message": message, "error": error}.items() if value}
    return RedirectResponse("/?" + urlencode(params) if params else "/", status_code=303)


def validate_name(name: str) -> str:
    name = " ".join(name.strip().split())
    if not NAME_PATTERN.fullmatch(name):
        raise ValueError("El nombre debe tener entre 2 y 60 letras; solo se permiten espacios, apóstrofes y guiones.")
    return name


def validate_roles(roles: list[str]) -> list[str]:
    selected = list(dict.fromkeys(roles))
    if not selected or any(role not in ROLES for role in selected):
        raise ValueError("Selecciona al menos un rol válido.")
    return selected


def validate_need(day: int, role: str, start: int, end: int, minimum: int) -> None:
    if day not in range(7) or role not in ROLES:
        raise ValueError("Selecciona un día y una función válidos.")
    if not (0 <= start < end <= 23):
        raise ValueError("El horario debe estar entre 00 y 23, y el final debe ser posterior al inicio.")
    if not 1 <= minimum <= 20:
        raise ValueError("La cobertura mínima debe estar entre 1 y 20 personas.")


def worker_models(db):
    return [Worker(e.id, e.name, frozenset(e.roles), {int(k): [tuple(slot) for slot in value] for k, value in e.availability.items()}, e.max_hours, e.opening, e.closing) for e in db.query(Employee).all()]


def seed() -> None:
    init_db()
    db = session()
    if not db.query(Employee).count():
        for name, roles in DEMO:
            employee = Employee(name=name, max_hours=40, opening="Caja" in roles, closing="Supervisor" in roles)
            employee.roles = roles
            employee.availability = {str(day): [[8, 23]] for day in range(7)}
            db.add(employee)
        for day in range(7):
            for role in ("Caja", "Cocina", "Servicio"):
                db.add(OperationalNeed(day=day, role=role, start=12, end=16, minimum=1))
            db.add(OperationalNeed(day=day, role="Limpieza", start=16, end=20, minimum=1))
        db.commit()
    db.close()


seed()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = session()
    employees = db.query(Employee).order_by(Employee.name).all()
    needs = db.query(OperationalNeed).order_by(OperationalNeed.day, OperationalNeed.start, OperationalNeed.role).all()
    result = generate_schedule(worker_models(db), [Need(n.day, n.role, n.start, n.end, n.minimum) for n in needs])
    return templates.TemplateResponse(request=request, name="app.html", context={"employees": employees, "needs": needs, "result": result, "days": DAYS, "roles": ROLES, "message": request.query_params.get("message"), "error": request.query_params.get("error")})


@app.post("/generate")
def generate():
    db = session()
    result = generate_schedule(worker_models(db), [Need(n.day, n.role, n.start, n.end, n.minimum) for n in db.query(OperationalNeed).all()])
    saved = SavedSchedule(status="generated" if result.feasible else "infeasible")
    db.add(saved)
    db.flush()
    for assignment in result.assignments:
        db.add(AssignmentRow(schedule_id=saved.id, employee_id=assignment.worker_id, day=assignment.day, role=assignment.role, start=assignment.start, end=assignment.end, special=assignment.special))
    db.commit()
    db.close()
    return redirect("Horario generado y guardado." if result.feasible else "No fue posible generar un horario completo.")


@app.post("/employees")
def add_employee(name: str = Form(...), roles: list[str] = Form(...), max_hours: int = Form(40), opening: bool = Form(False), closing: bool = Form(False)):
    try:
        name, roles = validate_name(name), validate_roles(roles)
        if not 1 <= max_hours <= 80: raise ValueError("El máximo semanal debe estar entre 1 y 80 horas.")
        db = session()
        if db.query(Employee).filter(Employee.name.ilike(name)).first():
            db.close(); return redirect(error="Ya existe una persona con ese nombre.")
        employee = Employee(name=name, max_hours=max_hours, opening=opening, closing=closing)
        employee.roles, employee.availability = roles, {str(day): [[8, 23]] for day in range(7)}
        db.add(employee); db.commit(); db.close()
        return redirect("Persona añadida al equipo.")
    except ValueError as exc:
        return redirect(error=str(exc))


@app.post("/employees/{employee_id}/edit")
def edit_employee(employee_id: int, max_hours: int = Form(40), roles: list[str] = Form(...), opening: bool = Form(False), closing: bool = Form(False)):
    try:
        roles = validate_roles(roles)
        if not 1 <= max_hours <= 80: raise ValueError("El máximo semanal debe estar entre 1 y 80 horas.")
        db = session(); employee = db.get(Employee, employee_id)
        if not employee: raise HTTPException(404, "Empleado no encontrado")
        employee.roles, employee.max_hours, employee.opening, employee.closing = roles, max_hours, opening, closing
        db.commit(); db.close(); return redirect("Perfil actualizado.")
    except ValueError as exc:
        return redirect(error=str(exc))


@app.post("/employees/{employee_id}/delete")
def delete_employee(employee_id: int):
    db = session(); employee = db.get(Employee, employee_id)
    if employee: db.delete(employee); db.commit()
    db.close(); return redirect("Persona eliminada del sistema.")


@app.post("/needs")
def add_need(day: int = Form(...), role: str = Form(...), start: int = Form(...), end: int = Form(...), minimum: int = Form(1)):
    try:
        validate_need(day, role, start, end, minimum)
        db = session(); db.add(OperationalNeed(day=day, role=role, start=start, end=end, minimum=minimum)); db.commit(); db.close()
        return redirect("Cobertura añadida.")
    except ValueError as exc:
        return redirect(error=str(exc))


@app.post("/needs/{need_id}/edit")
def edit_need(need_id: int, day: int = Form(...), role: str = Form(...), start: int = Form(...), end: int = Form(...), minimum: int = Form(1)):
    try:
        validate_need(day, role, start, end, minimum)
        db = session(); need = db.get(OperationalNeed, need_id)
        if not need: raise HTTPException(404, "Cobertura no encontrada")
        need.day, need.role, need.start, need.end, need.minimum = day, role, start, end, minimum
        db.commit(); db.close(); return redirect("Cobertura actualizada.")
    except ValueError as exc:
        return redirect(error=str(exc))


@app.post("/needs/{need_id}/delete")
def delete_need(need_id: int):
    db = session(); need = db.get(OperationalNeed, need_id)
    if need: db.delete(need); db.commit()
    db.close(); return redirect("Cobertura eliminada.")
