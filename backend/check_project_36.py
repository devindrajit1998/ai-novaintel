from db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if project exists
    result = conn.execute(text("SELECT id, name, owner_id FROM projects WHERE id = 36"))
    project = result.fetchone()
    
    if project:
        print(f"[OK] Project 36 exists")
        print(f"  Name: {project[1]}")
        print(f"  Owner ID: {project[2]}")
    else:
        print("[ERROR] Project 36 does NOT exist")
        exit(1)
    
    # Check if insights exist
    result = conn.execute(text("SELECT id, project_id, executive_summary, rfp_summary, proposal_draft FROM insights WHERE project_id = 36"))
    insights = result.fetchone()
    
    if insights:
        print(f"\n[OK] Insights EXIST for project 36")
        print(f"  Insights ID: {insights[0]}")
        print(f"  Has executive_summary: {insights[2] is not None}")
        print(f"  Has rfp_summary: {insights[3] is not None}")
        print(f"  Has proposal_draft: {insights[4] is not None}")
        print("\n[ISSUE] Insights exist in DB but endpoint returns 404!")
        print("  This indicates a different problem - likely authentication or serialization issue.")
    else:
        print(f"\n[INFO] No insights found for project 36")
        print("  The 404 is expected - run the agents workflow to generate insights.")
