import sys
import traceback

print("Testing vector store initialization...")
print("-" * 50)

try:
    from rag.vector_store import vector_store_manager
    
    print(f"Vector store available: {vector_store_manager.is_available()}")
    
    if vector_store_manager.is_available():
        print("[OK] Vector store initialized successfully!")
        print(f"Vector store instance: {vector_store_manager.vector_store}")
    else:
        print("[ERROR] Vector store is NOT available")
        print("Check the error messages above for details")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Exception during import/initialization: {e}")
    traceback.print_exc()
    sys.exit(1)
