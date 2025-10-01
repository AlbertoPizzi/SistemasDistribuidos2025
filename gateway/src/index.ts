import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const candidates = [
    // cuando corre compilado en Docker (/app/dist → /app/protos)
    path.join(__dirname, "../../protos/src/weatherapp.proto"),
    // cuando corre en dev desde la raíz del repo
    path.resolve(process.cwd(), "protos/src/weatherapp.proto"),
];

const PROTO_PATH = candidates.find(p => fs.existsSync(p)) || candidates[0];

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: false,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
});

const weatherappPkg = (grpc.loadPackageDefinition(packageDefinition) as any).weatherapp;

const ip2locClient = new weatherappPkg.IP2Location(
    process.env.IP2LOC_ADDR || "ip2location-svc:50051",
    grpc.credentials.createInsecure()
);

const weatherClient = new weatherappPkg.Weather(
    process.env.WEATHER_ADDR || "weather-svc:50052",
    grpc.credentials.createInsecure()
);

const app = express();
const port = Number(process.env.PORT || 8080);

function extractClientIp(req: express.Request): string {
    const xfwd = (req.headers["x-forwarded-for"] as string) || "";
    if (xfwd) return xfwd.split(",")[0].trim();
    const ip = req.socket.remoteAddress || "";
    return ip.replace("::ffff:", "");
}

app.get("/health", (_req, res) => res.json({ ok: true }));

app.get("/weather", async (req, res) => {
    const ip = (req.query.ip as string) || "";
    try {
        const loc = await new Promise<any>((resolve, reject) => {
            ip2locClient.Resolve({ ip }, (err: any, data: any) =>
                err ? reject(err) : resolve(data)
            );
        });

        let { lat, lon } = loc || {};
        if ((lat === 0 && lon === 0) || lat == null || lon == null) {
            const clientIp = ip || extractClientIp(req);
            const retry = await new Promise<any>((resolve, reject) => {
                ip2locClient.Resolve({ ip: clientIp }, (err: any, data: any) =>
                    err ? reject(err) : resolve(data)
                );
            });
            if (!retry?.lat || !retry?.lon) {
                return res.status(400).json({ error: "Unable to resolve IP location" });
            }
            lat = retry.lat;
            lon = retry.lon;
            const w = await new Promise<any>((resolve, reject) => {
                weatherClient.Current({ lat, lon }, (err: any, data: any) =>
                    err ? reject(err) : resolve(data)
                );
            });
            return res.json({ ip: clientIp, location: retry, weather: w });
        }

        const w = await new Promise<any>((resolve, reject) => {
            weatherClient.Current({ lat, lon }, (err: any, data: any) =>
                err ? reject(err) : resolve(data)
            );
        });

        res.json({ ip: ip || extractClientIp(req), location: loc, weather: w });
    } catch (e: any) {
        console.error(e);
        const code = e?.code === grpc.status.UNAVAILABLE ? 503 : 500;
        res.status(code).json({ error: e?.details || e?.message || "internal error" });
    }
});

app.listen(port, () => {
    console.log(`[gateway] HTTP listening on :${port}`);
});
