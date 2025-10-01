import os
import json
import logging
from concurrent import futures

import grpc
import requests

import weatherapp_pb2
import weatherapp_pb2_grpc


IPWHO_URL = os.getenv("IPWHO_URL", "https://ipwho.is/")
PORT = int(os.getenv("PORT", "50051"))


logging.basicConfig(level=logging.INFO, format="[ip2location] %(levelname)s: %(message)s")


class IP2LocationServicer(weatherapp_pb2_grpc.IP2LocationServicer):
    def Resolve(self, request, context):
        ip = (request.ip or "").strip()
        url = IPWHO_URL + (ip if ip else "")
        logging.info(f"Resolving IP: '{ip}' via {url}")
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            if not data.get("success", True):
                # ipwho.is devuelve success=false con message
                msg = data.get("message", "Unknown error from ipwho.is")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(f"ipwho.is error: {msg}")
                return weatherapp_pb2.LocationReply()


            lat = float(data.get("latitude"))
            lon = float(data.get("longitude"))
            city = data.get("city", "")
            country = data.get("country", "")
            return weatherapp_pb2.LocationReply(lat=lat, lon=lon, city=city, country=country)
        except requests.RequestException as e:
            logging.exception("HTTP error calling ipwho.is")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"ipwho.is unavailable: {e}")
            return weatherapp_pb2.LocationReply()
        except (ValueError, KeyError) as e:
            logging.exception("Parsing error from ipwho.is response")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to parse ipwho.is response: {e}")
            return weatherapp_pb2.LocationReply()




def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    weatherapp_pb2_grpc.add_IP2LocationServicer_to_server(IP2LocationServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    logging.info(f"gRPC IP2Location service listening on :{PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()