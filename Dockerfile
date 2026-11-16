
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Criação de usuário sem privilégios administrativos
RUN addgroup --system app && adduser --system --ingroup app app

# Cópia dos arquivos com as permissões do novo usuário
COPY --chown=app:app . .

# A aplicação será executada como usuário comum
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
