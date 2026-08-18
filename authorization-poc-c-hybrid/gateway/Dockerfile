FROM python:3.13-slim
WORKDIR /app
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway/app.py .
COPY data/attributes.json /data/attributes.json
EXPOSE 8090
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8090"]
