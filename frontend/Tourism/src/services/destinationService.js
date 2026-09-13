// Thin re-export: your project's real "service layer" already lives at
// src/api/destinationApi.js (and src/services/api.js for photos) — this
// file exists only so components can `import destinationService from
// "../services/destinationService"` per the layering the spec asked
// for, WITHOUT forking the actual axios logic into a second copy.
export { default } from "../api/destinationApi"