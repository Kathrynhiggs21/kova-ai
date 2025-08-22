#!/usr/bin/env bash
set -euo pipefail

# 1) Find first package.json (monorepo-safe). Fall back to repo root.
APP_DIR="$(git ls-files **/package.json | grep -v node_modules | head -n 1 | xargs -I{} dirname {} || true)"
APP_DIR="${APP_DIR:-.}"

echo "Detected app directory: $APP_DIR"

# 2) Install Node deps if present
if [ -f "$APP_DIR/package.json" ]; then
  pushd "$APP_DIR" >/dev/null
  npm ci || npm i
  # Create helpful scripts if missing
  jq '."scripts" += {"dev":"vite || next dev || react-scripts start || node server.js","build":"vite build || next build || echo build","test":"echo no-tests && exit 0"}' package.json > package.tmp.json || true
  mv -f package.tmp.json package.json || true
  popd >/dev/null
else
  # Optional: bootstrap an empty project so CI/Codespace don’t fail
  npm init -y
  npm pkg set scripts.dev="echo 'no dev server yet'"
  npm pkg set scripts.build="echo 'no build yet'"
  npm pkg set scripts.test="echo 'no tests' && exit 0"
fi

# 3) Quality-of-life tools
npm i -g npm@latest yarn pnpm

echo "Post-create complete."
