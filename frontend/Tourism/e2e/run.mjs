#!/usr/bin/env node
import { spawn } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

const here = path.dirname(fileURLToPath(import.meta.url))
const live = spawn(process.execPath, [path.join(here, "live.mjs")], {
  cwd: path.resolve(here, ".."),
  stdio: "inherit",
  env: process.env,
})
live.on("exit", (code) => process.exit(code || 0))
