"""SQLite persistence for the demo and web application."""
import json
from datetime import datetime
from sqlalchemy import create_engine, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL = "sqlite:///./rosterflow.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Employee(Base):
    __tablename__="employees"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(100)); roles_json: Mapped[str]=mapped_column(Text, default="[]")
    opening: Mapped[bool]=mapped_column(Boolean, default=False); closing: Mapped[bool]=mapped_column(Boolean, default=False); max_hours: Mapped[int]=mapped_column(Integer, default=40); availability_json: Mapped[str]=mapped_column(Text, default="{}")
    @property
    def roles(self): return json.loads(self.roles_json)
    @roles.setter
    def roles(self, v): self.roles_json=json.dumps(v, ensure_ascii=False)
    @property
    def availability(self): return json.loads(self.availability_json)
    @availability.setter
    def availability(self, v): self.availability_json=json.dumps(v)
class OperationalNeed(Base):
    __tablename__="operational_needs"
    id: Mapped[int]=mapped_column(primary_key=True); day: Mapped[int]=mapped_column(Integer); role: Mapped[str]=mapped_column(String(50)); start: Mapped[int]=mapped_column(Integer); end: Mapped[int]=mapped_column(Integer); minimum: Mapped[int]=mapped_column(Integer, default=1)
class SavedSchedule(Base):
    __tablename__="schedules"
    id: Mapped[int]=mapped_column(primary_key=True); created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow); status: Mapped[str]=mapped_column(String(20), default="generated")
class AssignmentRow(Base):
    __tablename__="assignments"
    id: Mapped[int]=mapped_column(primary_key=True); schedule_id: Mapped[int]=mapped_column(ForeignKey("schedules.id")); employee_id: Mapped[int]=mapped_column(ForeignKey("employees.id")); day: Mapped[int]=mapped_column(Integer); role: Mapped[str]=mapped_column(String(50)); start: Mapped[int]=mapped_column(Integer); end: Mapped[int]=mapped_column(Integer); special: Mapped[str]=mapped_column(String(20), default="")
def init_db(): Base.metadata.create_all(engine)
def session() -> Session: return SessionLocal()
