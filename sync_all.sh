#!/usr/bin/env bash
set -euo pipefail

########################################
# EDIT THESE PATHS TO YOUR LOCAL FILES #
########################################
# Sources you want pushed into kova-ai
KOVA_README_SRC="$HOME/README.md"
KOVA_INTEGRATIONS_SRC="$HOME/integrations.md"
KOVA_FEEDBACK_SRC="$HOME/message_feedback.json"
KOVA_DRIVE_TRACKER_SRC="$HOME/KOVA_Access_Tracker_for_Drive.xlsx"   # (optional) Not recommended to keep in git
KOVA_SMART_DEVICE_JSON_SRC="$HOME/smartdevicemanagement_discovery.json"

# Wix Velo script for Scribbles
VELO_SRC="$HOME/scribbles-velo.js"

########################################
# REPO URLS (HTTPS; use SSH if you prefer)
########################################
KOVA_REPO_URL="https://github.com/Kathrynhiggs21/kova-ai.git"
SCRIBBLES_REPO_URL="https://github.com/Kathrynhiggs21/scribbles-velo.git"
SITE_REPO_URL="https://github.com/Kathrynhiggs21/kova-ai-site.git"

# Branch name to push
BRANCH="main"

info(){ printf "\n==> %s\n" "$*"; }
need(){ command -v "$1" >/dev/null || { echo "Missing $1. Install it and re-run."; exit 1; }; }
add_if_exists(){ local src="$1" dest="$2"; if [[ -f "$src" ]]; then mkdir -p "$(dirname "$dest")"; cp -f "$src" "$dest"; else echo "  (skip: $src not found)"; fi; }
ensure_repo(){
  local url="$1" dir="$2"
    if [[ -d "$dir/.git" ]]; then
        info "Pull latest in $dir"
            git -C "$dir" pull --rebase || true
              else
                  info "Clone $url → $dir"
                      git clone "$url" "$dir"
                        fi
                        }
                        commit_push(){
                          local dir="$1" msg="$2"
                            pushd "$dir" >/dev/null
                              git add -A
                                git commit -m "$msg" || echo "(nothing to commit)"
                                  git push -u origin "$BRANCH"
                                    popd >/dev/null
                                    }

                                    need git

                                    ########################################
                                    # 1) KOVA APP REPO
                                    ########################################
                                    ensure_repo "$KOVA_REPO_URL" "kova-ai"

                                    info "Copying files into kova-ai/"
                                    add_if_exists "$KOVA_README_SRC"            "kova-ai/README.md"
                                    add_if_exists "$KOVA_INTEGRATIONS_SRC"      "kova-ai/integrations.md"
                                    add_if_exists "$KOVA_FEEDBACK_SRC"          "kova-ai/message_feedback.json"
                                    # If you truly need the tracker in git, uncomment the next line,
                                    # but it's safer to store spreadsheets outside git.
                                    # add_if_exists "$KOVA_DRIVE_TRACKER_SRC"     "kova-ai/KOVA_Access_Tracker_for_Drive.xlsx"
                                    add_if_exists "$KOVA_SMART_DEVICE_JSON_SRC" "kova-ai/smartdevicemanagement_discovery.json"

                                    # Hygiene (safe to re-run)
                                    mkdir -p kova-ai/.github/workflows
                                    cat > kova-ai/.gitignore <<'EOF'
                                    # dependencies & build
                                    node_modules/
                                    dist/
                                    build/
                                    .DS_Store
                                    *.log

                                    # env & secrets (IMPORTANT)
                                    .env
                                    .env.*
                                    *.key
                                    *.pem
                                    *.p12
                                    *.docx
                                    *.xlsx
                                    EOF

                                    cat > kova-ai/.github/workflows/ci.yml <<'EOF'
                                    name: CI
                                    on: [push, pull_request]
                                    jobs:
                                      build:
                                          runs-on: ubuntu-latest
                                              steps:
                                                    - uses: actions/checkout@v4
                                                          - uses: actions/setup-node@v4
                                                                  with:
                                                                            node-version: 20
                                                                                      cache: 'npm'
                                                                                            - run: npm ci || npm install
                                                                                                  - run: npm run build --if-present
                                                                                                        - run: npm test --if-present
                                                                                                        EOF

                                                                                                        # Ensure a README exists
                                                                                                        if [[ ! -f kova-ai/README.md ]]; then
                                                                                                          cat > kova-ai/README.md <<'EOF'
                                                                                                          # KOVA-AI (App)
                                                                                                          Private codebase for the KOVA assistant.
                                                                                                          - Deploys: Netlify/Vercel from `main`
                                                                                                          - CI: GitHub Actions (build/test)
                                                                                                          - Secrets: store in Actions/hosting env; never commit .env or docs/xlsx
                                                                                                          EOF
                                                                                                          fi

                                                                                                          commit_push "kova-ai" "chore: sync KOVA (docs, configs, CI, .gitignore)"

                                                                                                          ########################################
                                                                                                          # 2) SCRIBBLES (WIX VELO) REPO
                                                                                                          ########################################
                                                                                                          ensure_repo "$SCRIBBLES_REPO_URL" "scribbles-velo"
                                                                                                          mkdir -p scribbles-velo/src

                                                                                                          info "Copying Velo script into scribbles-velo/src/"
                                                                                                          add_if_exists "$VELO_SRC" "scribbles-velo/src/scribbles-velo.js"

                                                                                                          # Lightweight README (only if missing)
                                                                                                          if [[ ! -f scribbles-velo/README.md ]]; then
                                                                                                            cat > scribbles-velo/README.md <<'EOF'
                                                                                                            # Scribbles by Marcy — Wix Velo
                                                                                                            This repo stores Wix Velo scripts for backup/version control.
                                                                                                            ⚠️ Velo code executes inside Wix; this repo won't run $w APIs.
                                                                                                            EOF
                                                                                                            fi

                                                                                                            # Keep hygiene consistent
                                                                                                            cat > scribbles-velo/.gitignore <<'EOF'
                                                                                                            node_modules/
                                                                                                            dist/
                                                                                                            build/
                                                                                                            .DS_Store
                                                                                                            *.log
                                                                                                            .env
                                                                                                            .env.*
                                                                                                            *.key
                                                                                                            *.pem
                                                                                                            *.p12
                                                                                                            *.docx
                                                                                                            *.xlsx
                                                                                                            EOF

                                                                                                            commit_push "scribbles-velo" "feat: update Velo script (src/scribbles-velo.js)"

                                                                                                            ########################################
                                                                                                            # 3) PUBLIC DOCS SITE (GitHub Pages → kovaos.com)
                                                                                                            ########################################
                                                                                                            ensure_repo "$SITE_REPO_URL" "kova-ai-site"
                                                                                                            mkdir -p kova-ai-site/.github/workflows kova-ai-site/docs

                                                                                                            # Pages workflow + minimal site (idempotent)
                                                                                                            cat > kova-ai-site/.github/workflows/pages.yml <<'EOF'
                                                                                                            name: Deploy GitHub Pages
                                                                                                            on:
                                                                                                              push: { branches: [ "main" ] }
                                                                                                                workflow_dispatch:
                                                                                                                permissions: { contents: read, pages: write, id-token: write }
                                                                                                                concurrency: { group: "pages", cancel-in-progress: true }
                                                                                                                jobs:
                                                                                                                  build:
                                                                                                                      runs-on: ubuntu-latest
                                                                                                                          steps:
                                                                                                                                - uses: actions/checkout@v4
                                                                                                                                      - uses: actions/upload-pages-artifact@v3
                                                                                                                                              with: { path: . }
                                                                                                                                                deploy:
                                                                                                                                                    needs: build
                                                                                                                                                        runs-on: ubuntu-latest
                                                                                                                                                            environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }
                                                                                                                                                                steps:
                                                                                                                                                                      - id: deployment
                                                                                                                                                                              uses: actions/deploy-pages@v4
                                                                                                                                                                              EOF

                                                                                                                                                                              # Custom domain
                                                                                                                                                                              echo "kovaos.com" > kova-ai-site/CNAME

                                                                                                                                                                              # Minimal site files if missing
                                                                                                                                                                              if [[ ! -f kova-ai-site/index.html ]]; then
                                                                                                                                                                                cat > kova-ai-site/index.html <<'EOF'
                                                                                                                                                                                <!doctype html><html lang="en"><head>
                                                                                                                                                                                <meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
                                                                                                                                                                                <title>KOVA — Public Docs</title>
                                                                                                                                                                                <link rel="stylesheet" href="styles.css"/></head>
                                                                                                                                                                                <body><main class="hero"><h1>KOVA‑AI</h1>
                                                                                                                                                                                <p>Public docs & links: <a href="docs/getting-started.md">Getting started</a> • <a href="docs/roadmap.md">Roadmap</a></p>
                                                                                                                                                                                </main></body></html>
                                                                                                                                                                                EOF
                                                                                                                                                                                fi
                                                                                                                                                                                if [[ ! -f kova-ai-site/styles.css ]]; then
                                                                                                                                                                                  cat > kova-ai-site/styles.css <<'EOF'
                                                                                                                                                                                  body{font-family:system-ui,Arial;margin:0;background:#0b0b0f;color:#eee;display:grid;place-items:center;height:100vh}
                                                                                                                                                                                  .hero{max-width:680px;text-align:center}
                                                                                                                                                                                  a{color:#FDE68A}
                                                                                                                                                                                  EOF
                                                                                                                                                                                  fi
                                                                                                                                                                                  if [[ ! -f kova-ai-site/docs/getting-started.md ]]; then
                                                                                                                                                                                    cat > kova-ai-site/docs/getting-started.md <<'EOF'
                                                                                                                                                                                    # Getting Started
                                                                                                                                                                                    This repo publishes to **kovaos.com** using GitHub Pages (via Actions).
                                                                                                                                                                                    EOF
                                                                                                                                                                                    fi
                                                                                                                                                                                    if [[ ! -f kova-ai-site/docs/roadmap.md ]]; then
                                                                                                                                                                                      cat > kova-ai-site/docs/roadmap.md <<'EOF'
                                                                                                                                                                                      # Roadmap
                                                                                                                                                                                      - Pages live + HTTPS
                                                                                                                                                                                      - Expand docs & examples
                                                                                                                                                                                      EOF
                                                                                                                                                                                      fi

                                                                                                                                                                                      commit_push "kova-ai-site" "feat: Pages workflow + CNAME(kovaos.com) + base docs"

                                                                                                                                                                                      echo
                                                                                                                                                                                      info "All done ✅  Next: In GitHub → kova-ai-site → Settings → Pages → ensure Source=GitHub Actions and Enforce HTTPS when available."
                                                                                                                                                                                      #!/usr/bin/env bash
                                                                                                                                                                                      set -euo pipefail

                                                                                                                                                                                      ########################################
                                                                                                                                                                                      # EDIT THESE PATHS TO YOUR LOCAL FILES #
                                                                                                                                                                                      ########################################
                                                                                                                                                                                      # Sources you want pushed into kova-ai
                                                                                                                                                                                      KOVA_README_SRC="$HOME/README.md"
                                                                                                                                                                                      KOVA_INTEGRATIONS_SRC="$HOME/integrations.md"
                                                                                                                                                                                      KOVA_FEEDBACK_SRC="$HOME/message_feedback.json"
                                                                                                                                                                                      KOVA_DRIVE_TRACKER_SRC="$HOME/KOVA_Access_Tracker_for_Drive.xlsx"   # (optional) Not recommended to keep in git
                                                                                                                                                                                      KOVA_SMART_DEVICE_JSON_SRC="$HOME/smartdevicemanagement_discovery.json"

                                                                                                                                                                                      # Wix Velo script for Scribbles
                                                                                                                                                                                      VELO_SRC="$HOME/scribbles-velo.js"

                                                                                                                                                                                      ########################################
                                                                                                                                                                                      # REPO URLS (HTTPS; use SSH if you prefer)
                                                                                                                                                                                      ########################################
                                                                                                                                                                                      KOVA_REPO_URL="https://github.com/Kathrynhiggs21/kova-ai.git"
                                                                                                                                                                                      SCRIBBLES_REPO_URL="https://github.com/Kathrynhiggs21/scribbles-velo.git"
                                                                                                                                                                                      SITE_REPO_URL="https://github.com/Kathrynhiggs21/kova-ai-site.git"

                                                                                                                                                                                      # Branch name to push
                                                                                                                                                                                      BRANCH="main"

                                                                                                                                                                                      info(){ printf "\n==> %s\n" "$*"; }
                                                                                                                                                                                      need(){ command -v "$1" >/dev/null || { echo "Missing $1. Install it and re-run."; exit 1; }; }
                                                                                                                                                                                      add_if_exists(){ local src="$1" dest="$2"; if [[ -f "$src" ]]; then mkdir -p "$(dirname "$dest")"; cp -f "$src" "$dest"; else echo "  (skip: $src not found)"; fi; }
                                                                                                                                                                                      ensure_repo(){
                                                                                                                                                                                        local url="$1" dir="$2"
                                                                                                                                                                                          if [[ -d "$dir/.git" ]]; then
                                                                                                                                                                                              info "Pull latest in $dir"
                                                                                                                                                                                                  git -C "$dir" pull --rebase || true
                                                                                                                                                                                                    else
                                                                                                                                                                                                        info "Clone $url → $dir"
                                                                                                                                                                                                            git clone "$url" "$dir"
                                                                                                                                                                                                              fi
                                                                                                                                                                                                              }
                                                                                                                                                                                                              commit_push(){
                                                                                                                                                                                                                local dir="$1" msg="$2"
                                                                                                                                                                                                                  pushd "$dir" >/dev/null
                                                                                                                                                                                                                    git add -A
                                                                                                                                                                                                                      git commit -m "$msg" || echo "(nothing to commit)"
                                                                                                                                                                                                                        git push -u origin "$BRANCH"
                                                                                                                                                                                                                          popd >/dev/null
                                                                                                                                                                                                                          }

                                                                                                                                                                                                                          need git

                                                                                                                                                                                                                          ########################################
                                                                                                                                                                                                                          # 1) KOVA APP REPO
                                                                                                                                                                                                                          ########################################
                                                                                                                                                                                                                          ensure_repo "$KOVA_REPO_URL" "kova-ai"

                                                                                                                                                                                                                          info "Copying files into kova-ai/"
                                                                                                                                                                                                                          add_if_exists "$KOVA_README_SRC"            "kova-ai/README.md"
                                                                                                                                                                                                                          add_if_exists "$KOVA_INTEGRATIONS_SRC"      "kova-ai/integrations.md"
                                                                                                                                                                                                                          add_if_exists "$KOVA_FEEDBACK_SRC"          "kova-ai/message_feedback.json"
                                                                                                                                                                                                                          # If you truly need the tracker in git, uncomment the next line,
                                                                                                                                                                                                                          # but it's safer to store spreadsheets outside git.
                                                                                                                                                                                                                          # add_if_exists "$KOVA_DRIVE_TRACKER_SRC"     "kova-ai/KOVA_Access_Tracker_for_Drive.xlsx"
                                                                                                                                                                                                                          add_if_exists "$KOVA_SMART_DEVICE_JSON_SRC" "kova-ai/smartdevicemanagement_discovery.json"

                                                                                                                                                                                                                          # Hygiene (safe to re-run)
                                                                                                                                                                                                                          mkdir -p kova-ai/.github/workflows
                                                                                                                                                                                                                          cat > kova-ai/.gitignore <<'EOF'
                                                                                                                                                                                                                          # dependencies & build
                                                                                                                                                                                                                          node_modules/
                                                                                                                                                                                                                          dist/
                                                                                                                                                                                                                          build/
                                                                                                                                                                                                                          .DS_Store
                                                                                                                                                                                                                          *.log

                                                                                                                                                                                                                          # env & secrets (IMPORTANT)
                                                                                                                                                                                                                          .env
                                                                                                                                                                                                                          .env.*
                                                                                                                                                                                                                          *.key
                                                                                                                                                                                                                          *.pem
                                                                                                                                                                                                                          *.p12
                                                                                                                                                                                                                          *.docx
                                                                                                                                                                                                                          *.xlsx
                                                                                                                                                                                                                          EOF

                                                                                                                                                                                                                          cat > kova-ai/.github/workflows/ci.yml <<'EOF'
                                                                                                                                                                                                                          name: CI
                                                                                                                                                                                                                          on: [push, pull_request]
                                                                                                                                                                                                                          jobs:
                                                                                                                                                                                                                            build:
                                                                                                                                                                                                                                runs-on: ubuntu-latest
                                                                                                                                                                                                                                    steps:
                                                                                                                                                                                                                                          - uses: actions/checkout@v4
                                                                                                                                                                                                                                                - uses: actions/setup-node@v4
                                                                                                                                                                                                                                                        with:
                                                                                                                                                                                                                                                                  node-version: 20
                                                                                                                                                                                                                                                                            cache: 'npm'
                                                                                                                                                                                                                                                                                  - run: npm ci || npm install
                                                                                                                                                                                                                                                                                        - run: npm run build --if-present
                                                                                                                                                                                                                                                                                              - run: npm test --if-present
                                                                                                                                                                                                                                                                                              EOF

                                                                                                                                                                                                                                                                                              # Ensure a README exists
                                                                                                                                                                                                                                                                                              if [[ ! -f kova-ai/README.md ]]; then
                                                                                                                                                                                                                                                                                                cat > kova-ai/README.md <<'EOF'
                                                                                                                                                                                                                                                                                                # KOVA-AI (App)
                                                                                                                                                                                                                                                                                                Private codebase for the KOVA assistant.
                                                                                                                                                                                                                                                                                                - Deploys: Netlify/Vercel from `main`
                                                                                                                                                                                                                                                                                                - CI: GitHub Actions (build/test)
                                                                                                                                                                                                                                                                                                - Secrets: store in Actions/hosting env; never commit .env or docs/xlsx
                                                                                                                                                                                                                                                                                                EOF
                                                                                                                                                                                                                                                                                                fi

                                                                                                                                                                                                                                                                                                commit_push "kova-ai" "chore: sync KOVA (docs, configs, CI, .gitignore)"

                                                                                                                                                                                                                                                                                                ########################################
                                                                                                                                                                                                                                                                                                # 2) SCRIBBLES (WIX VELO) REPO
                                                                                                                                                                                                                                                                                                ########################################
                                                                                                                                                                                                                                                                                                ensure_repo "$SCRIBBLES_REPO_URL" "scribbles-velo"
                                                                                                                                                                                                                                                                                                mkdir -p scribbles-velo/src

                                                                                                                                                                                                                                                                                                info "Copying Velo script into scribbles-velo/src/"
                                                                                                                                                                                                                                                                                                add_if_exists "$VELO_SRC" "scribbles-velo/src/scribbles-velo.js"

                                                                                                                                                                                                                                                                                                # Lightweight README (only if missing)
                                                                                                                                                                                                                                                                                                if [[ ! -f scribbles-velo/README.md ]]; then
                                                                                                                                                                                                                                                                                                  cat > scribbles-velo/README.md <<'EOF'
                                                                                                                                                                                                                                                                                                  # Scribbles by Marcy — Wix Velo
                                                                                                                                                                                                                                                                                                  This repo stores Wix Velo scripts for backup/version control.
                                                                                                                                                                                                                                                                                                  ⚠️ Velo code executes inside Wix; this repo won't run $w APIs.
                                                                                                                                                                                                                                                                                                  EOF
                                                                                                                                                                                                                                                                                                  fi

                                                                                                                                                                                                                                                                                                  # Keep hygiene consistent
                                                                                                                                                                                                                                                                                                  cat > scribbles-velo/.gitignore <<'EOF'
                                                                                                                                                                                                                                                                                                  node_modules/
                                                                                                                                                                                                                                                                                                  dist/
                                                                                                                                                                                                                                                                                                  build/
                                                                                                                                                                                                                                                                                                  .DS_Store
                                                                                                                                                                                                                                                                                                  *.log
                                                                                                                                                                                                                                                                                                  .env
                                                                                                                                                                                                                                                                                                  .env.*
                                                                                                                                                                                                                                                                                                  *.key
                                                                                                                                                                                                                                                                                                  *.pem
                                                                                                                                                                                                                                                                                                  *.p12
                                                                                                                                                                                                                                                                                                  *.docx
                                                                                                                                                                                                                                                                                                  *.xlsx
                                                                                                                                                                                                                                                                                                  EOF

                                                                                                                                                                                                                                                                                                  commit_push "scribbles-velo" "feat: update Velo script (src/scribbles-velo.js)"

                                                                                                                                                                                                                                                                                                  ########################################
                                                                                                                                                                                                                                                                                                  # 3) PUBLIC DOCS SITE (GitHub Pages → kovaos.com)
                                                                                                                                                                                                                                                                                                  ########################################
                                                                                                                                                                                                                                                                                                  ensure_repo "$SITE_REPO_URL" "kova-ai-site"
                                                                                                                                                                                                                                                                                                  mkdir -p kova-ai-site/.github/workflows kova-ai-site/docs

                                                                                                                                                                                                                                                                                                  # Pages workflow + minimal site (idempotent)
                                                                                                                                                                                                                                                                                                  cat > kova-ai-site/.github/workflows/pages.yml <<'EOF'
                                                                                                                                                                                                                                                                                                  name: Deploy GitHub Pages
                                                                                                                                                                                                                                                                                                  on:
                                                                                                                                                                                                                                                                                                    push: { branches: [ "main" ] }
                                                                                                                                                                                                                                                                                                      workflow_dispatch:
                                                                                                                                                                                                                                                                                                      permissions: { contents: read, pages: write, id-token: write }
                                                                                                                                                                                                                                                                                                      concurrency: { group: "pages", cancel-in-progress: true }
                                                                                                                                                                                                                                                                                                      jobs:
                                                                                                                                                                                                                                                                                                        build:
                                                                                                                                                                                                                                                                                                            runs-on: ubuntu-latest
                                                                                                                                                                                                                                                                                                                steps:
                                                                                                                                                                                                                                                                                                                      - uses: actions/checkout@v4
                                                                                                                                                                                                                                                                                                                            - uses: actions/upload-pages-artifact@v3
                                                                                                                                                                                                                                                                                                                                    with: { path: . }
                                                                                                                                                                                                                                                                                                                                      deploy:
                                                                                                                                                                                                                                                                                                                                          needs: build
                                                                                                                                                                                                                                                                                                                                              runs-on: ubuntu-latest
                                                                                                                                                                                                                                                                                                                                                  environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }
                                                                                                                                                                                                                                                                                                                                                      steps:
                                                                                                                                                                                                                                                                                                                                                            - id: deployment
                                                                                                                                                                                                                                                                                                                                                                    uses: actions/deploy-pages@v4
                                                                                                                                                                                                                                                                                                                                                                    EOF

                                                                                                                                                                                                                                                                                                                                                                    # Custom domain
                                                                                                                                                                                                                                                                                                                                                                    echo "kovaos.com" > kova-ai-site/CNAME

                                                                                                                                                                                                                                                                                                                                                                    # Minimal site files if missing
                                                                                                                                                                                                                                                                                                                                                                    if [[ ! -f kova-ai-site/index.html ]]; then
                                                                                                                                                                                                                                                                                                                                                                      cat > kova-ai-site/index.html <<'EOF'
                                                                                                                                                                                                                                                                                                                                                                      <!doctype html><html lang="en"><head>
                                                                                                                                                                                                                                                                                                                                                                      <meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
                                                                                                                                                                                                                                                                                                                                                                      <title>KOVA — Public Docs</title>
                                                                                                                                                                                                                                                                                                                                                                      <link rel="stylesheet" href="styles.css"/></head>
                                                                                                                                                                                                                                                                                                                                                                      <body><main class="hero"><h1>KOVA‑AI</h1>
                                                                                                                                                                                                                                                                                                                                                                      <p>Public docs & links: <a href="docs/getting-started.md">Getting started</a> • <a href="docs/roadmap.md">Roadmap</a></p>
                                                                                                                                                                                                                                                                                                                                                                      </main></body></html>
                                                                                                                                                                                                                                                                                                                                                                      EOF
                                                                                                                                                                                                                                                                                                                                                                      fi
                                                                                                                                                                                                                                                                                                                                                                      if [[ ! -f kova-ai-site/styles.css ]]; then
                                                                                                                                                                                                                                                                                                                                                                        cat > kova-ai-site/styles.css <<'EOF'
                                                                                                                                                                                                                                                                                                                                                                        body{font-family:system-ui,Arial;margin:0;background:#0b0b0f;color:#eee;display:grid;place-items:center;height:100vh}
                                                                                                                                                                                                                                                                                                                                                                        .hero{max-width:680px;text-align:center}
                                                                                                                                                                                                                                                                                                                                                                        a{color:#FDE68A}
                                                                                                                                                                                                                                                                                                                                                                        EOF
                                                                                                                                                                                                                                                                                                                                                                        fi
                                                                                                                                                                                                                                                                                                                                                                        if [[ ! -f kova-ai-site/docs/getting-started.md ]]; then
                                                                                                                                                                                                                                                                                                                                                                          cat > kova-ai-site/docs/getting-started.md <<'EOF'
                                                                                                                                                                                                                                                                                                                                                                          # Getting Started
                                                                                                                                                                                                                                                                                                                                                                          This repo publishes to **kovaos.com** using GitHub Pages (via Actions).
                                                                                                                                                                                                                                                                                                                                                                          EOF
                                                                                                                                                                                                                                                                                                                                                                          fi
                                                                                                                                                                                                                                                                                                                                                                          if [[ ! -f kova-ai-site/docs/roadmap.md ]]; then
                                                                                                                                                                                                                                                                                                                                                                            cat > kova-ai-site/docs/roadmap.md <<'EOF'
                                                                                                                                                                                                                                                                                                                                                                            # Roadmap
                                                                                                                                                                                                                                                                                                                                                                            - Pages live + HTTPS
                                                                                                                                                                                                                                                                                                                                                                            - Expand docs & examples
                                                                                                                                                                                                                                                                                                                                                                            EOF
                                                                                                                                                                                                                                                                                                                                                                            fi

                                                                                                                                                                                                                                                                                                                                                                            commit_push "kova-ai-site" "feat: Pages workflow + CNAME(kovaos.com) + base docs"

                                                                                                                                                                                                                                                                                                                                                                            echo
                                                                                                                                                                                                                                                                                                                                                                            info "All done ✅  Next: In GitHub → kova-ai-site → Settings → Pages → ensure Source=GitHub Actions and Enforce HTTPS when available."
                                                                                                                                                                                                                                                                                                                                                                            

































