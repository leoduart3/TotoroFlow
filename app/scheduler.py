"""Pure scheduling engine using OR-Tools CP-SAT."""
from dataclasses import dataclass
from ortools.sat.python import cp_model

@dataclass(frozen=True)
class Worker:
    id: int; name: str; roles: frozenset[str]; availability: dict[int, list[tuple[int,int]]]
    max_hours: int = 40; opening: bool = False; closing: bool = False

@dataclass(frozen=True)
class Need:
    day: int; role: str; start: int; end: int; minimum: int

@dataclass(frozen=True)
class Assignment:
    worker_id: int; worker: str; day: int; role: str; start: int; end: int; special: str = ""

@dataclass
class ScheduleResult:
    assignments: list[Assignment]; feasible: bool; conflicts: list[str]

def generate_schedule(workers: list[Worker], needs: list[Need], opening: dict[int,int]|None=None, closing: dict[int,int]|None=None) -> ScheduleResult:
    model=cp_model.CpModel(); vars=[]; slots=[]
    for n in needs:
        for w in workers:
            if n.role not in w.roles: continue
            if not any(a<=n.start and n.end<=b for a,b in w.availability.get(n.day, [])): continue
            v=model.NewBoolVar(f"w{w.id}d{n.day}r{n.role}s{n.start}"); vars.append(v); slots.append((v,w,n))
    for w in workers:
        mine=[(v,n) for v,ww,n in slots if ww.id==w.id]
        model.Add(sum(v*(n.end-n.start) for v,n in mine)<=w.max_hours)
        for i,(v,n) in enumerate(mine):
            for ov,on in mine[i+1:]:
                if n.day==on.day and n.start<on.end and on.start<n.end: model.Add(v+ov<=1)
    for n in needs:
        chosen=[v for v,w,nn in slots if nn==n]; model.Add(sum(chosen)>=n.minimum)
    # Prefer fewer assignments and balanced hours (coverage is hard).
    model.Minimize(sum(vars))
    solver=cp_model.CpSolver(); solver.parameters.max_time_in_seconds=5
    status=solver.Solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return ScheduleResult([],False,["No existe una combinación que respete disponibilidad, roles, solapamientos y máximos de jornada."])
    out=[]
    for v,w,n in slots:
        if solver.Value(v): out.append(Assignment(w.id,w.name,n.day,n.role,n.start,n.end))
    return ScheduleResult(out,True,[])

