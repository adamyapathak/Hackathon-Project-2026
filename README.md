# Clemson Under the Stars

## Run backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn adamya.main:app --reload
```

Backend: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

## Run frontend

In a second terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Open: http://127.0.0.1:5500
