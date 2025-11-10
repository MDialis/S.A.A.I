# S.A.A.I
Sistema de Acompanhamento Alimentar Inteligente

Guia de primeira iniciação do projeto:
Em seu terminal digite:

- python -m venv venv
- .\venv\Scripts\activate
- pip install fastapi uvicorn sqlalchemy dotenv psycopg2 requests pillow google-generativeai python-multipart
- uvicorn app.main:app --reload