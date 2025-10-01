import os
import logging
from concurrent import futures

import grpc
import requests

import weatherapp_pb2
import weatherapp_pb2_grpc


OPEN_METEO_URL = os.getenv(
    "OPEN_METEO_URL",
    "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m,weather_code&timezone=auto"
)
PORT = int(os.getenv("PORT", "50052"))


logging.basicConfig(level=logging.INFO, format="[weather] %(levelname)s: %(message)s")


class WeatherServicer(weatherapp_pb2_grpc.WeatherServicer):
    def Current(self, request, context):
        lat = request.lat
        lon = request.lon
        url = f"{OPEN_METEO_URL}&latitude={lat}&longitude={lon}"
        logging.info(f"Fetching weather for lat={lat}, lon={lon}")
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            current = data.get("current", {})
            # Algunos endpoints usan claves distintas; aquí asumimos el schema nuevo de open-meteo
            time = current.get("time") or data.get("current_weather", {}).get("time", "")
            temp = current.get("temperature_2m") or data.get("current_weather", {}).get("temperature")
            wind = current.get("wind_speed_10m") or data.get("current_weather", {}).get("windspeed")
            code = current.get("weather_code") or data.get("current_weather", {}).get("weathercode")

            if temp is None or wind is None or code is None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Unexpected response from open-meteo")
                return weatherapp_pb2.WeatherReply()


            return weatherapp_pb2.WeatherReply(
                time=str(time),
                temperature=float(temp),
                windspeed=float(wind),
                weathercode=int(code),
            )
        except requests.RequestException as e:
            logging.exception("HTTP error calling open-meteo")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"open-meteo unavailable: {e}")
            return weatherapp_pb2.WeatherReply()




def serve():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        weatherapp_pb2_grpc.add_WeatherServicer_to_server(WeatherServicer(), server)
        server.add_insecure_port(f"[::]:{PORT}")
        server.start()
        logging.info(f"gRPC Weather service listening on :{PORT}")
        server.wait_for_termination()


if __name__ == "__main__":
    serve()