"""
WSGI entry point for PythonAnywhere manual configuration.
FastAPI is ASGI; a2wsgi bridges it to WSGI.
Use this only if 'pa website create' doesn't work.
"""
import os
import sys

path = "/home/ammarjamshed123/pak-bank-discounts-ai/backend"
if path not in sys.path:
    sys.path.insert(0, path)
os.chdir(path)

from dotenv import load_dotenv

load_dotenv(os.path.join(path, ".env"))

from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
