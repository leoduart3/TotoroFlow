from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .scheduler import *
app=FastAPI(title="RosterFlow"); templates=Jinja2Templates(directory="app/templates")
WORKERS=[Worker(i,n,frozenset(r),{d:[(8,23)] for d in range(7)},max_hours=40,opening="Caja" in r,closing="Supervisor" in r) for i,(n,r) in enumerate([
 ("Ana Torres",["Caja"]),("Bruno Silva",["Caja","Servicio"]),("Carla Méndez",["Cocina"]),("Diego Rojas",["Cocina"]),("Elena Paz",["Servicio"]),("Fabián Núñez",["Servicio","Bartender"]),("Gina Vera",["Limpieza"]),("Hugo Sosa",["Supervisor","Caja"]),("Iris Benítez",["Cocina","Limpieza"]),("Julián Acosta",["Servicio"]),("Karen Ortiz",["Cocina"]),("Leo Giménez",["Limpieza","Servicio"])])]
NEEDS=[Need(d,r,12,16,1) for d in range(7) for r in ["Caja","Cocina","Servicio"]]+[Need(d,"Limpieza",16,20,1) for d in range(7)]
@app.get("/",response_class=HTMLResponse)
def home(request:Request):
 result=generate_schedule(WORKERS,NEEDS); return templates.TemplateResponse("index.html",{"request":request,"workers":WORKERS,"result":result,"days":["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]})
@app.post("/generate")
def generate(): return RedirectResponse("/",status_code=303)
@app.post("/employees")
def add_employee(name:str=Form(...),role:str=Form(...)):
 WORKERS.append(Worker(len(WORKERS)+1,name,frozenset([role]),{d:[(8,23)] for d in range(7)})); return RedirectResponse("/",status_code=303)
