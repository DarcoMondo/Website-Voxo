#!/bin/bash
echo "Testing backend connection..."
curl -s http://localhost:8000/ || echo "Backend not responding on port 8000"
curl -s http://localhost:8000/health || echo "Health endpoint not responding"
echo "Done."

