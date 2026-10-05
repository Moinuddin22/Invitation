# Invitation: Haris & Mehreen

One app, two invitations, each with its own link and theme:

| Link | Event | Theme |
|---|---|---|
| `/nikah` | Nikah, 21 Nov 2026, St. Mary College Hall, Mumbai | Mughal maroon & gold, palace doors, lanterns, rose petals |
| `/valima` | Valima, 27 Nov 2026, Meridian Function Hall, Hyderabad | Nizami emerald & gold, wax-sealed envelope, Charminar skyline, jasmine |

Both share one backend, one RSVP form and one database (each RSVP is tagged with its event).

**Stack:** FastAPI, Jinja2, HTMX, Tailwind, SQLAlchemy (SQLite locally, PostgreSQL on AWS)

## Run on a new machine
Needs: git, [uv](https://docs.astral.sh/uv/). No `.env` needed: event details are in code and the DB defaults to SQLite.
```bash
git clone <repo-url> && cd Invitation
uv sync            # add the Walmart --index-url flags if on the corporate network
uv run uvicorn app.main:app --reload
# http://127.0.0.1:8000/nikah  and  http://127.0.0.1:8000/valima
uv run pytest -q
```

## Edit content
Everything lives in **`app/events.py`**: names, fathers, dates, times, venues, Quran verse per event.
Adding an event = one `Event(...)` entry + a theme (`static/css/themes/<x>.css` + `templates/themes/<x>/`).

## Structure
```
app/
  events.py      couple + events (content)
  main.py        routes: /{event}, POST /{event}/rsvp, /health
  config.py db.py models.py schemas.py
  templates/     base, index, shared section partials, themes/<theme>/{intro,decor}.html
  static/css/    base.css + themes/{nikah,valima}.css
infra/terraform/ ECR, App Runner, RDS Postgres, Secrets Manager, Route 53 domain
```

## AWS resources (created by Terraform)
| Resource | Purpose |
|---|---|
| ECR repository | stores the Docker image |
| App Runner service + VPC connector | runs the container, HTTPS, autoscaling |
| RDS PostgreSQL (db.t4g.micro, private) | RSVP storage |
| Secrets Manager secret | DB connection string (password auto-generated) |
| Security groups, IAM roles | only App Runner can reach the DB |
| Route 53 records + App Runner custom domain | your domain with a free TLS certificate |

Uses the account's default VPC. Rough cost: about $25-35/month plus the domain (~$13/yr for `.com`).

## Deploy
```bash
brew install terraform awscli
aws configure --profile <profile>
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars    # set aws_profile (+ domain_name once bought)
terraform init

# 1) registry, then push the image
terraform apply -target=aws_ecr_repository.app
REPO=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --profile <profile> --region ap-south-1 \
  | docker login --username AWS --password-stdin ${REPO%/*}
docker build --platform linux/amd64 -t $REPO:latest ../..
docker push $REPO:latest

# 2) everything else
terraform apply
# 3) only if domain_name is set: second apply adds the certificate validation records
terraform apply
terraform output invitation_links
```
Certificate validation takes ~5-30 min after step 3. Redeploying code = rebuild and push the image (App Runner auto-deploys).

### Domain
Buy it in **Route 53 > Registered domains** so the hosted zone is created automatically, then set
`domain_name` in `terraform.tfvars`. Links become `https://www.<domain>/nikah` and `/valima`.

### Teardown after the wedding
Set `deletion_protection = false` in `db.tf`, `terraform apply`, then `terraform destroy`.
A final DB snapshot is kept so RSVPs aren't lost.
