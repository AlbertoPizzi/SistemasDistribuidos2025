FROM node:20-alpine
WORKDIR /app

COPY gateway/package.json gateway/tsconfig.json ./
RUN npm install --omit=dev && npm cache clean --force
RUN npm install -D

COPY gateway/src ./src
COPY protos ./protos

# compilar a JS
RUN npx tsc

ENV PORT=8080 IP2LOC_ADDR=ip2location-svc:50051 WEATHER_ADDR=weather-svc:50052
EXPOSE 8080
CMD ["node", "dist/index.js"]
