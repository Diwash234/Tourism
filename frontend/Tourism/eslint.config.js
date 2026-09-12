import js from "@eslint/js"
import globals from "globals"
import reactHooks from "eslint-plugin-react-hooks"

export default [
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "e2e/**",
      // Known sandbox-leftover zombie files (deleted in P007, keep
      // resurrecting as untracked copies with broken exports). Gitignored
      // at the repo root; ignored here so a resurrection can never turn
      // `npm run lint` red again. See .gitignore "Dead broken duplicates".
      "src/pages/SmartImages.jsx",
      "src/pages/ImageGallery.jsx",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: { ...globals.browser, ...globals.node },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: { "react-hooks": reactHooks },
    rules: {
      // The rule family that catches "Rendered more hooks than during the
      // previous render" class bugs (conditional/loop hooks).
      ...reactHooks.configs.recommended.rules,
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrors: "none" }],
    },
  },
]
