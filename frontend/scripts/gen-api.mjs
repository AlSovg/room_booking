// OpenAPI из FastAPI без запуска сервера → типы в src/api/schema.d.ts
import { execFileSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const backend = new URL("../../backend/", import.meta.url);
const venv = ["Scripts/python.exe", "bin/python"].map((p) => new URL(`.venv/${p}`, backend)).find(existsSync);
const py = venv ? fileURLToPath(venv) : "python";
const json = execFileSync(py, ["-c", "import json;from app.main import app;print(json.dumps(app.openapi()))"], {
  cwd: fileURLToPath(backend),
});
writeFileSync("openapi.json", json);
execFileSync("npx", ["openapi-typescript", "openapi.json", "-o", "src/api/schema.d.ts"], { stdio: "inherit", shell: true });
