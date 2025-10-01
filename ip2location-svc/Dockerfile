FROM python:3.12-slim
WORKDIR /app

COPY ip2location-svc/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY protos ./protos
RUN mkdir -p ./src && \
    python -m grpc_tools.protoc \
      -I./protos/src \
      --python_out=./src \
      --grpc_python_out=./src \
      ./protos/src/weatherapp.proto

COPY ip2location-svc/src ./src
ENV PYTHONPATH=/app/src PORT=50051 IPWHO_URL=https://ipwho.is/
EXPOSE 50051
CMD ["python", "src/server.py"]
