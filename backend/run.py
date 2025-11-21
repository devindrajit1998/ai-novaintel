#!/usr/bin/env python3
"""
Development server runner for NovaIntel API
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("[INFO] Starting NovaIntel API server...")
    print("[INFO] Server will be available at http://localhost:8000")
    print("[INFO] API docs available at http://localhost:8000/docs")
    print("[INFO] Press CTRL+C to stop the server\n")
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",  # Use localhost instead of 0.0.0.0 for better compatibility
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Server failed to start: {e}")
        sys.exit(1)

