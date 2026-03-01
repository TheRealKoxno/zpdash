# GitHub Pages Setup

## 1. Prepare static dashboard files

Run:

```bash
cd /Users/ilyazenno/Desktop/zp_dumper
./prepare_github_pages.sh
```

This creates:

- `docs/index.html`
- `docs/dashboard.html`
- `docs/*.csv`
- `docs/dashboard_report.md`

## 2. Create/connect GitHub repository

If this folder is not a git repo yet:

```bash
cd /Users/ilyazenno/Desktop/zp_dumper
git init
git checkout -b main
git add .
git commit -m "Add Zenno dashboard + GitHub Pages deployment"
git remote add origin https://github.com/<your_user>/<your_repo>.git
git push -u origin main
```

If repo already exists, just commit/push.

## 3. Enable Pages in GitHub

In repository settings:

- `Settings` -> `Pages`
- `Build and deployment` -> `Source` = `GitHub Actions`

After push to `main`, workflow `.github/workflows/deploy-pages.yml` will publish `docs/`.

## 4. Open dashboard

URL format:

`https://<your_user>.github.io/<your_repo>/`

or

`https://<your_user>.github.io/<your_repo>/dashboard.html`

## Update flow

Whenever data changes:

```bash
cd /Users/ilyazenno/Desktop/zp_dumper
./prepare_github_pages.sh
git add docs dashboard_output analyze_dumper.py build_local_dashboard.py
git commit -m "Update dashboard data"
git push
```
