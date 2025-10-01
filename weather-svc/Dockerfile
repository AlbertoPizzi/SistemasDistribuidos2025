FROM python:3.12-slim
WORKDIR /app

COPY weather-svc/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY protos ./protos
# 👇 crear /app/src ANTES de correr protoc + incluir -I correcto
RUN mkdir -p ./src && \
    python -m grpc_tools.protoc \
      -I./protos/src \
      --python_out=./src \
      --grpc_python_out=./src \
      ./protos/src/weatherapp.proto

COPY weather-svc/src ./src
ENV PYTHONPATH=/app/src PORT=50052
EXPOSE 50052
CMD ["python", "src/server.py"]
