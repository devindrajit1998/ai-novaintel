from db.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
print("Insights table columns:")
cols = inspector.get_columns('insights')
for c in cols:
    print(f"  - {c['name']} ({c['type']})")
