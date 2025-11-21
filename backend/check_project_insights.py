from db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if project exists
    result = conn.execute(text("SELECT id, name, owner_id FROM projects WHERE id = 35"))
    project = result.fetchone()
    
    if project:
        print(f"[OK] Project 35 exists")
        print(f"  Name: {project[1]}")
        print(f"  Owner ID: {project[2]}")
    else:
        print("[ERROR] Project 35 does NOT exist")
        exit(1)
    
    # Check if insights exist
    result = conn.execute(text("SELECT id, project_id, executive_summary, rfp_summary, proposal_draft FROM insights WHERE project_id = 35"))
    insights = result.fetchone()
    
    if insights:
        print(f"\n[OK] Insights exist for project 35")
        print(f"  Insights ID: {insights[0]}")
        print(f"  Has executive_summary: {insights[2] is not None}")
        print(f"  Has rfp_summary: {insights[3] is not None}")
        print(f"  Has proposal_draft: {insights[4] is not None}")
    else:
        print(f"\n[ERROR] No insights found for project 35")
        print("  This is why you're getting a 404 error!")
        print("  You need to run the agents workflow first to generate insights.")
