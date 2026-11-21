from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db import Base

def utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    staging_url = Column(String)
    github_repo_url = Column(String)
    expected_endpoints = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    runs = relationship("AuditRun", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("RegressionAlert", back_populates="project", cascade="all, delete-orphan")

class AuditRun(Base):
    __tablename__ = "audit_runs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String, default="pending")
    readiness_score = Column(Integer, default=0)
    avg_latency_ms = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="runs")
    check_results = relationship("CheckResult", back_populates="audit_run", cascade="all, delete-orphan")

class CheckResult(Base):
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True, index=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"))
    category = Column(String)
    check_name = Column(String)
    status = Column(String)
    latency_ms = Column(Integer, default=0)
    details = Column(JSON, default=dict)
    severity_weight = Column(Integer, default=10)

    audit_run = relationship("AuditRun", back_populates="check_results")

class RegressionAlert(Base):
    __tablename__ = "regression_alerts"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"))
    check_name = Column(String)
    previous_status = Column(String)
    current_status = Column(String)
    message = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="alerts")