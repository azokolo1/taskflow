"""Generates the TaskFlow architecture diagram as SVG (rendered to PNG with rsvg-convert)."""
from xml.sax.saxutils import escape

W, H = 2100, 1390
FONT = "Inter, DejaVu Sans, sans-serif"

C = {
    "net": "#8C4FFF", "compute": "#ED7100", "db": "#3B48CC", "sec": "#DD344C",
    "mgmt": "#E7157B", "storage": "#7AA116", "ext": "#24292F", "graf": "#F46800",
    "req": "#2563EB", "deploy": "#7C3AED", "tel": "#EA580C", "egress": "#6B7280",
    "ink": "#111827", "muted": "#4B5563", "line": "#9CA3AF",
}

out = []
add = out.append


def text(x, y, s, size=12, weight=400, fill=C["muted"], anchor="start", italic=False):
    st = ' font-style="italic"' if italic else ""
    add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}"{st}>{escape(s)}</text>')


def container(x, y, w, h, label, color, fill="none", dash="", sub=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{color}" stroke-width="1.6"{d}/>')
    text(x + 12, y + 20, label, 13, 700, color)
    if sub:
        text(x + 12, y + 36, sub, 11, 400, C["muted"])


def box(x, y, w, h, title, lines=(), color=C["ink"], dashed=False, tag=None):
    d = ' stroke-dasharray="7 5"' if dashed else ""
    op = ' opacity="0.75"' if dashed else ""
    add(f'<g{op}>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#FFFFFF" stroke="{color}" stroke-width="1.6"{d}/>')
    add(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{color}"/>')
    text(x + 16, y + 22, title, 14.5, 700, C["ink"])
    if tag:
        text(x + w - 10, y + 20, tag, 10.5, 600, color, "end")
    for i, ln in enumerate(lines):
        text(x + 16, y + 42 + i * 17, ln, 12, 400, C["muted"])
    add('</g>')


def arrow(points, color, dash="", width=2.2, marker=None):
    m = marker or color.strip("#")
    pts = " ".join(f"{px},{py}" for px, py in points)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"{d} '
        f'stroke-linejoin="round" marker-end="url(#m{m})"/>')


def badge(x, y, label, color):
    add(f'<circle cx="{x}" cy="{y}" r="11" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>')
    text(x, y + 4.5, label, 12, 700, "#FFFFFF", "middle")


# ---------- document ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>")
for col in ("req", "deploy", "tel", "egress"):
    hx = C[col].strip("#")
    add(f'<marker id="m{hx}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{C[col]}"/></marker>')
add("</defs>")
add(f'<rect width="{W}" height="{H}" fill="#F8FAFC"/>')

text(30, 48, "TaskFlow — AWS Architecture (lab build, production-style)", 26, 800, C["ink"])
text(30, 74, "FastAPI + PostgreSQL on ECS Fargate · Terraform · GitHub Actions with OIDC · Prometheus/Grafana + CloudWatch",
     14, 400, C["muted"])

# ---------- AWS account / region / VPC ----------
container(360, 92, 1280, 1285, "AWS Account", "#232F3E", fill="#FFFFFF")
container(380, 228, 1245, 1137, "Region: eu-west-2 (London)", "#147EBA", fill="#F5FAFF")
container(400, 282, 830, 1070, "VPC 10.0.0.0/16", C["net"], fill="#FBF9FF")

# AZ columns
for x, name in ((418, "Availability Zone A"), (828, "Availability Zone B")):
    add(f'<rect x="{x}" y="318" width="390" height="1022" rx="8" fill="none" stroke="#147EBA" stroke-width="1.2" stroke-dasharray="4 4"/>')
    text(x + 195, 336, name, 12, 600, "#147EBA", "middle")

# subnets
subnets = [
    (350, 220, "Public subnet", ("10.0.1.0/24", "10.0.2.0/24"), "#E8F5E9", "#2E7D32"),
    (585, 290, "Private app subnet", ("10.0.11.0/24", "10.0.12.0/24"), "#E3F2FD", "#1565C0"),
    (890, 280, "Private DB subnet", ("10.0.21.0/24", "10.0.22.0/24"), "#E3F2FD", "#1565C0"),
]
for y, h, label, cidrs, fill, stroke in subnets:
    for i, x in enumerate((428, 838)):
        add(f'<rect x="{x}" y="{y}" width="370" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        text(x + 10, y + 16, f"{label} {cidrs[i]}", 11, 600, stroke)

# Internet gateway straddling VPC edge
box(690, 262, 165, 42, "Internet Gateway", color=C["net"])

# ALB spanning both public subnets
box(445, 392, 745, 70, "Application Load Balancer (internet-facing)",
    ["Listener :443 (TLS, ACM cert) · :80 → 301 redirect · target group health check GET /health"],
    color=C["net"], tag="sg-alb")

box(445, 482, 160, 74, "NAT Gateway", ["outbound only", "(lab: 1 total)"], color=C["net"])
box(637, 482, 155, 74, "EC2 lab host", ["Ubuntu · Linux drills", "access via SSM"], color=C["compute"])
box(1035, 482, 155, 74, "NAT Gateway", ["prod: one per AZ"], color=C["net"], dashed=True)

# ECS service + tasks
add('<rect x="440" y="610" width="760" height="258" rx="10" fill="none" stroke="#ED7100" stroke-width="1.4" stroke-dasharray="9 5"/>')



def task(x, dashed=False):
    box(x, 640, 335, 215, "ECS task (Fargate)", [], color=C["compute"], dashed=dashed, tag="sg-app")
    op = ' opacity="0.75"' if dashed else ""
    add(f'<g{op}>')
    add(f'<rect x="{x+16}" y="676" width="303" height="78" rx="6" fill="#FFF4E5" stroke="#ED7100"/>')
    text(x + 28, 696, "taskflow-api container", 13, 700, C["ink"])
    text(x + 28, 714, "FastAPI · uvicorn · :8000 · non-root", 11.5)
    text(x + 28, 731, "/health  /metrics  /api/v1/tasks", 11.5)
    text(x + 28, 747, "DB creds injected from Secrets Manager", 11.5)
    add(f'<rect x="{x+16}" y="764" width="303" height="78" rx="6" fill="#FFF4E5" stroke="#ED7100"/>')
    text(x + 28, 784, "collector sidecar", 13, 700, C["ink"])
    text(x + 28, 802, "ADOT / Grafana Alloy", 11.5)
    text(x + 28, 819, "scrapes localhost:8000/metrics", 11.5)
    text(x + 28, 836, "→ Prometheus remote_write", 11.5)
    add('</g>')


task(455)
task(850)

# RDS
box(455, 945, 335, 125, "Amazon RDS for PostgreSQL", [
    "Primary · private, not publicly accessible",
    "Encrypted at rest · TLS in transit",
    "Automated backups + snapshots",
    "Restore tested into a scratch instance"], color=C["db"], tag="sg-db")
box(850, 945, 335, 125, "RDS standby (Multi-AZ)", [
    "prod option: synchronous replica",
    "automatic failover",
    "lab: single-AZ to save cost"], color=C["db"], dashed=True)

# Security-group + lab-vs-prod panel
add('<rect x="428" y="1185" width="780" height="148" rx="8" fill="#FFFFFF" stroke="#D1D5DB"/>')
text(442, 1207, "Security group chain (each layer only accepts traffic from the layer in front of it)", 12.5, 700, C["ink"])
text(442, 1228, "sg-alb: allow 443/80 from 0.0.0.0/0   →   sg-app: allow 8000 from sg-alb only   →   sg-db: allow 5432 from sg-app only", 12)
text(442, 1256, "Lab vs production", 12.5, 700, C["ink"])
text(442, 1277, "Lab (affordable): 1 NAT gateway, single-AZ RDS, 1 task, short log retention, torn down when idle.", 12)
text(442, 1296, "Production-style: NAT per AZ, Multi-AZ RDS, ≥2 tasks across AZs, autoscaling, WAF, rollback on failed deploy.", 12)
text(442, 1315, "Dashed outline = production option, not built in the lab. Not HA until built and failover-tested.", 12, 400, C["muted"], italic=True)

# ---------- global row (inside account, outside region) ----------
box(470, 110, 255, 72, "Route 53", ["api.<your-domain> → ALB alias", "public hosted zone"], color=C["net"], tag="global")
box(990, 110, 240, 72, "AWS Budgets", ["monthly cost alerts", "→ email / SNS"], color=C["mgmt"], tag="global")
box(1265, 110, 350, 108, "IAM · OIDC provider · STS", [
    "OIDC provider: token.actions.githubusercontent.com",
    "Roles: gha-ci (read/plan) · gha-deploy (env-locked)",
    "ECS task role · task execution role"], color=C["sec"], tag="global")

# ---------- regional services column ----------
box(1265, 286, 340, 82, "Amazon ECR", ["private repo taskflow-api", "immutable tags (git SHA) · scan on push"], color=C["compute"])
box(1265, 388, 340, 82, "Secrets Manager", ["DB credentials (never in Git / images)", "read by task execution role at start"], color=C["sec"])
box(1265, 490, 340, 66, "ACM", ["TLS certificate for the ALB (DNS-validated)"], color=C["sec"])
box(1265, 604, 340, 176, "Amazon CloudWatch", [
    "Logs: /ecs/taskflow-api (awslogs driver)",
    "Metrics: ALB 5xx/latency, ECS CPU/mem,",
    "   RDS connections/storage, Container Insights",
    "Alarms: user-impact signals → SNS",
    "Retention set deliberately (cost)",
    ], color=C["mgmt"])
box(1265, 836, 340, 108, "Amazon S3", [
    "Terraform remote state (versioned, encrypted)",
    "native state locking (use_lockfile)",
    "ALB access logs bucket",
    ], color=C["storage"])
box(1265, 966, 340, 66, "Amazon SNS", ["alert topic → email / on-call"], color=C["mgmt"])
box(1265, 1054, 340, 66, "AWS CloudTrail", ["audit trail of API calls (who did what)"], color=C["mgmt"])

# ---------- outside AWS: left ----------
box(30, 112, 300, 96, "Users / API clients", ["Browser, curl, mobile app", "HTTPS only"], color=C["ext"])
box(30, 900, 300, 300, "Local development", [
    "Ubuntu laptop / VM",
    "",
    "Docker Compose (compose.yaml):",
    "  • api  — FastAPI (multi-stage image)",
    "  • db   — PostgreSQL + named volume",
    "  • prometheus — scrapes api:8000",
    "  • grafana — local dashboards",
    "",
    "pytest · ruff · alembic migrations",
    "git push → GitHub (PR-based)",
    "",
    "Same image runs locally and in ECS",
], color=C["ext"])

# ---------- outside AWS: right ----------
box(1690, 112, 380, 360, "GitHub", [
    "Repo: taskflow (branch protection on main)",
    "",
    "Actions — CI (every PR):",
    "  lint → test → build image → Trivy scan",
    "  terraform fmt / validate / plan",
    "",
    "Actions — CD (merge to main):",
    "  OIDC → assume gha-deploy role",
    "  push image :<git-sha> to ECR",
    "  register task definition (pinned digest)",
    "  update ECS service → wait for stable",
    "  smoke-test /health → report status",
    "",
    "Environment 'production': required reviewer",
    "No long-lived AWS keys stored anywhere",
], color=C["ext"])
box(1690, 704, 380, 150, "Grafana Cloud", [
    "Prometheus-compatible metrics store",
    "Dashboards: req rate · p95 latency · error %",
    "   CPU/mem · DB connections · deployments",
    "SLO-based alert rules (burn rate)",
    "(CloudWatch data source optional)",
], color=C["graf"])
box(1690, 920, 380, 66, "On-call engineer (you)", ["runbooks in docs/runbooks/ · postmortems"], color=C["ext"])

# ---------- arrows: request path ----------
arrow([(330, 146), (468, 146)], C["req"]); badge(400, 146, "1", C["req"])
arrow([(330, 192), (346, 192), (346, 205), (772, 205), (772, 259)], C["req"]); badge(560, 205, "2", C["req"])
arrow([(772, 304), (772, 390)], C["req"])
arrow([(622, 462), (622, 638)], C["req"]); badge(622, 570, "3", C["req"])
arrow([(1013, 462), (1013, 638)], C["req"]); badge(1013, 570, "3", C["req"])
arrow([(622, 855), (622, 943)], C["req"]); badge(622, 925, "4", C["req"])
arrow([(1013, 855), (1013, 880), (720, 880), (720, 943)], C["req"]); badge(870, 880, "4", C["req"])

# ---------- arrows: deploy path ----------
arrow([(1690, 165), (1617, 165)], C["deploy"]); badge(1652, 165, "A", C["deploy"])
arrow([(1690, 327), (1607, 327)], C["deploy"]); badge(1652, 327, "B", C["deploy"])
arrow([(1690, 440), (1660, 440), (1660, 580), (1214, 580), (1214, 640), (1202, 640)], C["deploy"]); badge(1440, 580, "C", C["deploy"])

# ---------- arrows: telemetry ----------
arrow([(1185, 712), (1263, 712)], C["tel"]); badge(1222, 712, "L", C["tel"])
arrow([(1185, 812), (1688, 812)], C["tel"]); badge(1440, 812, "M", C["tel"])
arrow([(1265, 768), (1248, 768), (1248, 999), (1263, 999)], C["tel"])
arrow([(1605, 999), (1688, 960)], C["tel"])
arrow([(1880, 854), (1880, 918)], C["tel"])

# ---------- arrows: egress ----------
arrow([(600, 640), (600, 578), (525, 578), (525, 558)], C["egress"], dash="5 4", width=1.8); badge(562, 578, "E", C["egress"])

# ECS service label, drawn above arrows on a white pill
add('<rect x="680" y="616" width="276" height="18" rx="9" fill="#FFFFFF" stroke="#ED7100" stroke-width="1"/>')
text(818, 629, "ECS Fargate service · taskflow-api", 11.5, 700, C["compute"], "middle")

# ---------- legend ----------
lx, ly = 1690, 1040
add(f'<rect x="{lx}" y="{ly}" width="380" height="337" rx="8" fill="#FFFFFF" stroke="#D1D5DB"/>')
text(lx + 14, ly + 24, "How to read this diagram", 14, 700, C["ink"])
rows = [
    ("1", C["req"], "Client resolves api.<domain> via Route 53"),
    ("2", C["req"], "HTTPS :443 via IGW to ALB; TLS ends at ALB"),
    ("3", C["req"], "ALB forwards to a healthy task on :8000"),
    ("4", C["req"], "App queries RDS on :5432 over TLS; reply returns"),
    ("A", C["deploy"], "GitHub OIDC token → STS temporary credentials"),
    ("B", C["deploy"], "CD pushes immutable image tagged with git SHA"),
    ("C", C["deploy"], "New task definition → ECS rolling deployment"),
    ("L", C["tel"], "Container logs → CloudWatch Logs"),
    ("M", C["tel"], "Collector remote_writes metrics → Grafana Cloud"),
    ("E", C["egress"], "Outbound via NAT: ECR pull, Secrets, Logs*"),
]
for i, (b, col, desc) in enumerate(rows):
    yy = ly + 50 + i * 24
    badge(lx + 26, yy - 4, b, col)
    text(lx + 46, yy, desc, 12, 400, C["ink"])
text(lx + 14, ly + 300, "Alarms → SNS / Grafana alerts → on-call (orange).", 11.5, 400, C["muted"])
text(lx + 14, ly + 318, "*VPC interface endpoints can replace NAT for AWS APIs.", 11.5, 400, C["muted"], italic=True)

add("</svg>")

with open("/home/claude/diagram/taskflow-architecture.svg", "w") as f:
    f.write("\n".join(out))
print("ok")
