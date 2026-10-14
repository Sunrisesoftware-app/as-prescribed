# Deploy: the public demo

https://asprescribed.sunrisesoftware.app, in replay mode (adr.ap.010). Decided in
[`DECISIONS.md`](../docs/DECISIONS.md) row 15.

```
browser ──https──> Cloudflare: Worker as-prescribed-edge (custom domain: DNS record and certificate)
                     └─ Workers VPC service as-prescribed-app ──> the machine's Cloudflare tunnel
                          └─> 127.0.0.1:8300 on the ultragravel machine: uvicorn, systemd unit as-prescribed
```

No port is opened on the machine and no certificate lives there: the tunnel (the existing
`cloudflared` service, shared with the machine's other services) dials out to Cloudflare. If that
tunnel is deleted or replaced, recreate the VPC service with the new tunnel id and update
`edge/wrangler.jsonc`.

| Where | What |
|---|---|
| ultragravel machine (Hetzner 135.181.157.185, Ubuntu 24.04, `ssh quaesitor` as root) | `/opt/as-prescribed/app`: the checkout of `main` (public repo, https), with `.venv` from `uv sync --frozen --no-dev` |
| | `/opt/as-prescribed/uv`: a venv holding only uv (the machine has no system uv) |
| | `/etc/systemd/system/as-prescribed.service`: [`as-prescribed.service`](as-prescribed.service) |
| Cloudflare (the owner's account, which also holds the sunrisesoftware.app zone and the tunnel) | Worker `as-prescribed-edge`: [`edge/`](edge/) |
| | VPC service `as-prescribed-app` (01a13b87-952e-7ac3-a845-1a5bf440c2b3): http, 127.0.0.1:8300, tunnel ca8faa27-55ac-4da4-9bf6-87d0b1753055 |

Nothing about a session is logged: uvicorn runs with `--no-access-log` and the Worker has
observability off.

## First install on the machine

```bash
git clone https://github.com/Sunrisesoftware-app/as-prescribed.git /opt/as-prescribed/app
python3 -m venv /opt/as-prescribed/uv
/opt/as-prescribed/uv/bin/pip install uv==0.11.29
cd /opt/as-prescribed/app && UV_PYTHON_DOWNLOADS=never /opt/as-prescribed/uv/bin/uv sync --frozen --no-dev
cp /opt/as-prescribed/app/deploy/as-prescribed.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now as-prescribed
```

## The edge (wrangler 4.124 or newer, logged in to the account)

```bash
wrangler vpc service create as-prescribed-app --type http --tunnel-id ca8faa27-55ac-4da4-9bf6-87d0b1753055 --ipv4 127.0.0.1 --http-port 8300
```

```bash
cd deploy/edge && wrangler deploy
```

## Update the app

```bash
cd /opt/as-prescribed/app && git pull --ff-only
UV_PYTHON_DOWNLOADS=never /opt/as-prescribed/uv/bin/uv sync --frozen --no-dev
systemctl restart as-prescribed
curl -fsS https://asprescribed.sunrisesoftware.app/health
```
