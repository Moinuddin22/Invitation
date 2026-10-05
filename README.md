# Invitation: Haris & Mehreen

Nikah invitation web app: intro with palace doors that open, Islamic welcome, couple names,
event and countdown, venue with an embedded Google Map, and an RSVP form saved to a relational DB.

**Stack:** FastAPI · Jinja2 · HTMX · Tailwind · SQLAlchemy (SQLite locally, PostgreSQL/RDS on AWS)

## Run locally
```bash
uv sync --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
uv run uvicorn app.main:app --reload
# open http://127.0.0.1:8000
uv run pytest -q
```

## Customize
Wedding date, time, and venue live in `app/config.py` and can be overridden with env vars (see `.env.example`).
Parents' names are placeholders (`________`) in `app/templates/partials/section_couple.html`.

## Structure
```
app/
  main.py        routes: /, POST /rsvp, /health
  config.py      settings (single source of truth)
  db.py models.py schemas.py
  templates/     base + one partial per section
  static/        invitation.css, invitation.js
infra/terraform/ ECR + App Runner + RDS Postgres + Secrets Manager
```

## Deploy to AWS (Terraform)
Architecture: **App Runner** (container, HTTPS out of the box) → VPC connector → **RDS PostgreSQL** (private).
The DB URL is generated and stored in **Secrets Manager**. Nothing is hard-coded.

```bash
brew install terraform awscli
aws configure --profile <your-profile>
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # set aws_profile + wedding details
terraform init

# 1) create the registry first
terraform apply -target=aws_ecr_repository.app
REPO=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --profile <your-profile> --region ap-south-1 \
  | docker login --username AWS --password-stdin ${REPO%/*}
docker build --platform linux/amd64 -t $REPO:latest ../..
docker push $REPO:latest

# 2) everything else
terraform apply
terraform output app_url
```
Rough cost: RDS db.t4g.micro + App Runner 0.25 vCPU is about $25–35/month. Run `terraform destroy` after the wedding
(turn off `deletion_protection` first).
