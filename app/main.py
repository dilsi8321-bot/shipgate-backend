from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models, db

app = FastAPI()

# Configure CORS Middleware for your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://shipgate-frontend-2yht0o4pa-dilsi8321-8750.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class ProjectCreate(BaseModel):
    name: str
    staging_url: str
    github_repo_url: str
    expected_endpoints: List[str] = []

class ProjectResponse(ProjectCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Startup Event to Initialize Tables ---
@app.on_event("startup")
async def startup():
    async with db.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

# --- API Routes ---
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(session: AsyncSession = Depends(db.get_db)):
    result = await session.execute(select(models.Project))
    projects = result.scalars().all()
    return projects

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, session: AsyncSession = Depends(db.get_db)):
    db_project = models.Project(
        name=project.name,
        staging_url=project.staging_url,
        github_repo_url=project.github_repo_url,
        expected_endpoints=project.expected_endpoints,
    )
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    return db_project
