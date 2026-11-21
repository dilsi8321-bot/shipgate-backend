import asyncio
from sqlalchemy import select
from app.db import AsyncSessionLocal, Base, engine
from app.models import AuditRun, CheckResult, Project, RegressionAlert, utc_now


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(Project))).scalars().all()
        if existing:
            print("Database already has projects; skipping duplicate seed.")
            return

        healthy = Project(
            name="Hackathon Starter API",
            staging_url="https://httpbin.org/get",
            github_repo_url="https://github.com/tiangolo/fastapi",
            expected_endpoints=[{"path": "/status/200"}],
        )
        broken = Project(
            name="Risky Demo App",
            staging_url="https://httpbin.org/status/500",
            github_repo_url="https://github.com/pallets/flask",
            expected_endpoints=[{"path": "/delay/4"}],
        )
        db.add_all([healthy, broken])
        await db.flush()

        run_good = AuditRun(
            project_id=healthy.id,
            status="completed",
            readiness_score=92,
            avg_latency_ms=180,
            completed_at=utc_now(),
        )
        run_bad = AuditRun(
            project_id=broken.id,
            status="completed",
            readiness_score=45,
            avg_latency_ms=2850,
            completed_at=utc_now(),
        )
        db.add_all([run_good, run_bad])
        await db.flush()

        db.add_all([
            CheckResult(
                audit_run_id=run_good.id,
                category="endpoint",
                check_name="Staging Root Health",
                status="pass",
                latency_ms=180,
                details={"status_code": 200},
                severity_weight=20,
            ),
            CheckResult(
                audit_run_id=run_bad.id,
                category="endpoint",
                check_name="Staging Root Health",
                status="fail",
                latency_ms=420,
                details={"status_code": 500, "fix_hint": "Check server logs for unhandled exception on root route."},
                severity_weight=20,
            ),
        ])

        db.add(
            RegressionAlert(
                project_id=broken.id,
                audit_run_id=run_bad.id,
                check_name="Staging Root Health",
                previous_status="pass",
                current_status="fail",
                message="Staging Root Health regressed from pass to fail.",
                resolved=False,
            )
        )

        await db.commit()
        print("Seeded 2 demo projects, runs, check results, and 1 regression alert.")


if __name__ == "__main__":
    asyncio.run(seed())
