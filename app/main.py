from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .scheduler import *
from .db import *
app=FastAPI(title="RosterFlow"); templates=Jinja2Templates(directory="app/templates"); app.mount("/static", StaticFiles(directory="app/static"), name="static")
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
 db=session(); employees=db.query(Employee).all(); needs=db.query(OperationalNeed).all(); result=generate_schedule(worker_models(db),[Need(n.day,n.role,n.start,n.end,n.minimum) for n in needs]); return templates.TemplateResponse(request=request,name="app.html",context={"workers":employees,"needs":needs,"result":result,"days":["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]})
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
@app.post("/needs")
def add_need(day:int=Form(...),role:str=Form(...),start:int=Form(...),end:int=Form(...),minimum:int=Form(1)):
 db=session(); db.add(OperationalNeed(day=day,role=role,start=start,end=end,minimum=minimum)); db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/needs/{need_id}/edit")
def edit_need(need_id:int,day:int=Form(...),role:str=Form(...),start:int=Form(...),end:int=Form(...),minimum:int=Form(1)):
 db=session(); n=db.get(OperationalNeed,need_id)
 if not n: raise HTTPException(404,"Need not found")
 n.day=day; n.role=role; n.start=start; n.end=end; n.minimum=minimum; db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/needs/{need_id}/delete")
def delete_need(need_id:int):
 db=session(); n=db.get(OperationalNeed,need_id)
 if n: db.delete(n); db.commit()
 db.close(); return RedirectResponse("/",status_code=303)
@app.post("/assignments/{assignment_id}/edit")
def edit_assignment(assignment_id:int,employee_id:int=Form(...),day:int=Form(...),role:str=Form(...),start:int=Form(...),end:int=Form(...)):
 db=session(); a=db.get(AssignmentRow,assignment_id)
 if not a: raise HTTPException(404,"Assignment not found")
 a.employee_id=employee_id; a.day=day; a.role=role; a.start=start; a.end=end; db.commit(); db.close(); return RedirectResponse("/",status_code=303)
@app.post("/assignments/{assignment_id}/delete")
def delete_assignment(assignment_id:int):
 db=session(); a=db.get(AssignmentRow,assignment_id)
 if a: db.delete(a); db.commit()
 db.close(); return RedirectResponse("/",status_code=303)
