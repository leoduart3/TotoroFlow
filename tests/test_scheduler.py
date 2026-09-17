from app.scheduler import *
def w(i,roles=["Caja"],av=None,max_hours=40): return Worker(i,"W",frozenset(roles),av or {0:[(8,18)]},max_hours)
def test_role_and_availability():
 r=generate_schedule([w(1)], [Need(0,"Caja",10,12,1)]); assert r.feasible and r.assignments[0].worker_id==1
 assert not generate_schedule([w(1,["Cocina"])],[Need(0,"Caja",10,12,1)]).feasible
def test_no_overlap():
 r=generate_schedule([w(1)], [Need(0,"Caja",10,12,1),Need(0,"Caja",11,13,1)]); assert not r.feasible
def test_max_hours(): assert not generate_schedule([w(1,max_hours=2)],[Need(0,"Caja",8,11,1)]).feasible
def test_coverage(): assert not generate_schedule([], [Need(0,"Caja",10,12,1)]).feasible
