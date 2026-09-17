from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .scheduler import *
from .db import *
app=FastAPI(title="RosterFlow"); templates=Jinja2Templates(directory="app/templates")
DEMO=[( "Ana Torres",["Caja"]),("Bruno Silva",["Caja","Servicio"]),("Carla Méndez",["Cocina"]),("Diego Rojas",["Cocina"]),("Elena Paz",["Servicio"]),("Fabián Núñez",["Servicio","Bartender"]),("Gina Vera",["Limpieza"]),("Hugo Sosa",["Supervisor","Caja"]),("Iris Benítez",["Cocina","Limpieza"]),("Julián Acosta",["Servicio"]),("Karen Ortiz",["Cocina"]),("Leo Giménez",["Limpieza","Servicio"])]
def seed():
 init_db(); db=session()
 if db.query(Employee).count()==0:
  for n,r in DEMO:
   e=Employee(name=n, max_hours=40, opening="Caja" in r, closing="Supervisor" in r); e.roles=r; e.availability={str(d):[[8,23]] for d in range(7)}; db.add(e)
  for d in range(7):
   for role in ["Caja","Cocina","Servicio"]: db.add(OperationalNeed(day=d,role=role,start=12,end=16,minimum=1))
   db.add(OperationalNeed(day=d,role="Limpieza",start=16,end=20,minimum=1))
  db.commit()
 db.close()
seed()
def worker_models(db):
 return [Worker(e.id,e.name,frozenset(e.roles),{int(k):[tuple(x) for x in v] for k,v in e.availability.items()},e.max_hours,e.opening,e.closing) for e in db.query(Employee).all()]
@app.get("/",response_class=HTMLResponse)
def home(request:Request):
 db=session(); employees=db.query(Employee).all(); needs=db.query(OperationalNeed).all(); result=generate_schedule(worker_models(db),[Need(n.day,n.role,n.start,n.end,n.minimum) for n in needs]); return templates.TemplateResponse(request=request,name="dashboard.html",context={"workers":employees,"result":result,"days":["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]})
@app.post("/generate")
def generate():
 db=session(); result=generate_schedule(worker_models(db),[Need(n.day,n.role,n.start,n.end,n.minimum) for n in db.query(OperationalNeed).all()]); schedule=SavedSchedule(status="generated" if result.feasible else "infeasible"); db.add(schedule); db.flush()
 for a in result.assignments: db.add(AssignmentRow(schedule_id=schedule.id,employee_id=a.worker_id,day=a.day,role=a.role,start=a.start,end=a.end,special=a.special))
 db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/employees")
def add_employee(name:str=Form(...),role:str=Form(...),max_hours:int=Form(40),opening:bool=Form(False),closing:bool=Form(False)):
 db=session(); e=Employee(name=name,max_hours=max_hours,opening=opening,closing=closing); e.roles=[role]; e.availability={str(d):[[8,23]] for d in range(7)}; db.add(e); db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/employees/{employee_id}/edit")
def edit_employee(employee_id:int,name:str=Form(...),roles:str=Form(...),max_hours:int=Form(40),opening:bool=Form(False),closing:bool=Form(False)):
 db=session(); e=db.get(Employee,employee_id)
 if not e: raise HTTPException(404,"Employee not found")
 e.name=name; e.roles=[x.strip() for x in roles.split(",") if x.strip()]; e.max_hours=max_hours; e.opening=opening; e.closing=closing; db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/employees/{employee_id}/delete")
def delete_employee(employee_id:int):
 db=session(); e=db.get(Employee,employee_id)
 if e: db.delete(e); db.commit()
 db.close(); return RedirectResponse("/",status_code=303)
