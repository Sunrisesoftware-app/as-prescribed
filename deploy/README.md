# Deploy: the public demo

https://asprescribed.sunrisesoftware.app runs each case live on AMD Token Factory (Qwen3.8-27B drafting,
Gemma-4-31B-IT checking) and compares it with the same case recorded on the clinic hardware. It serves
that recording when the cloud fails or takes longer than `AP_LIVE_BUDGET_S` (90 s). Decided in
[`DECISIONS.md`](../docs/DECISIONS.md) rows 15, 22 and 23.

```
browser ──https──> Cloudflare: Worker as-prescribed-edge (custom domain: DNS record and certificate)
                     └─ Workers VPC service as-prescribed-app ──> the machine's Cloudflare tunnel
                          └─> 127.0.0.1:8300 on the ultragravel machine: uvicorn, systemd unit as-prescribed
                               └─https──> AMD Token Factory (developer.amd.com.cn/radeon/api/v1)
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
| | `/etc/as-prescribed/env` (root, 0600, not in git): `AP_LIVE_BUDGET_S=90`, the two endpoints and models (`GENERATOR_THINKING_PARAM=true` turns Qwen's thinking off per call), `TOKENFACTORY_BASE_URL` and `TOKENFACTORY_API_KEY`. `AP_REPLAY=1` there switches back to replay only. |
| Cloudflare (the owner's account, which also holds the sunrisesoftware.app zone and the tunnel) | Worker `as-prescribed-edge`: [`edge/`](edge/) |
| | VPC service `as-prescribed-app` (01a13b87-952e-7ac3-a845-1a5bf440c2b3): http, 127.0.0.1:8300, tunnel ca8faa27-55ac-4da4-9bf6-87d0b1753055 |

Nothing about a session is logged here: uvicorn runs with `--no-access-log` and the Worker has
observability off. Token Factory keeps prompts and outputs for about two days (its terms). The demo
sends only the synthetic sessions, and those terms forbid real health data, which is why a clinic
runs the same pipeline on its own Radeon cards.

## First install on the machine

```bash
git clone https://github.com/Sunrisesoftware-app/as-prescribed.git /opt/as-prescribed/app
python3 -m venv /opt/as-prescribed/uv
/opt/as-prescribed/uv/bin/pip install uv==0.11.29
cd /opt/as-prescribed/app && UV_PYTHON_DOWNLOADS=never /opt/as-prescribed/uv/bin/uv sync --frozen --no-dev
cp /opt/as-prescribed/app/deploy/as-prescribed.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now as-prescribed
```

The key file is written from the owner's local `.env` over ssh, so the key is never printed or typed:
the two `TOKENFACTORY_` lines are piped to the machine, which adds the endpoints, models and budget.

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
