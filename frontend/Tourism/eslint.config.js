import js from "@eslint/js"
import globals from "globals"
import reactHooks from "eslint-plugin-react-hooks"

export default [
  { ignores: ["dist/**", "node_modules/**", "e2e/**"] },
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
