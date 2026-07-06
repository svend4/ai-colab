# Dev Setup Guide

## Requirements
* Python 3.11+
* Git

## Initial Setup
1. Clone the repository and navigate to it:
   ```bash
   git clone <repo_url> "New project ai colab"
   cd "New project ai colab"
   ```

2. Set up virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. Install requirements (currently standard library is heavily utilized, but pytest is needed for full testing):
   ```bash
   pip install -r requirements.txt
   ```

## Verifying the Setup
Run the smoke tests to ensure the environment is correctly configured and the repository canon is healthy:

```bash
python smoke.py
```

If it prints `Smoke tests passed successfully. The environment is healthy.`, you are ready to work.