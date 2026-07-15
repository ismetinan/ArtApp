venv/bin/uvicorn app.main:app --reload --host 0.0.0.0

fuser -k 8000/tcp

flutter run -d 4870494a --dart-define=API_BASE=http://[IP_ADDRESS]