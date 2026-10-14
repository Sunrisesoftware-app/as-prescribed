# Deploy: the public demo

asprescribed.sunrisesoftware.app on the ultragravel machine (Hetzner 135.181.157.185, Ubuntu 24.04,
`ssh quaesitor` as root), in replay mode (adr.ap.010): uvicorn on 127.0.0.1:8300 as a systemd unit,
nginx and a Let's Encrypt certificate in front, Cloudflare DNS. Decided in
[`DECISIONS.md`](../docs/DECISIONS.md) row 15.

| Path on the machine | What |
|---|---|
| `/opt/as-prescribed/app` | The checkout of `main` (public repo, https), with `.venv` from `uv sync --frozen --no-dev` |
| `/opt/as-prescribed/uv` | A venv holding only uv (the machine has no system uv) |
| `/etc/systemd/system/as-prescribed.service` | [`as-prescribed.service`](as-prescribed.service) |
| `/etc/nginx/sites-available/as-prescribed` | [`nginx.conf`](nginx.conf), plus what certbot adds |

## First install

```bash
git clone https://github.com/Sunrisesoftware-app/as-prescribed.git /opt/as-prescribed/app
python3 -m venv /opt/as-prescribed/uv
/opt/as-prescribed/uv/bin/pip install uv==0.11.29
cd /opt/as-prescribed/app && UV_PYTHON_DOWNLOADS=never /opt/as-prescribed/uv/bin/uv sync --frozen --no-dev
cp /opt/as-prescribed/app/deploy/as-prescribed.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now as-prescribed
cp /opt/as-prescribed/app/deploy/nginx.conf /etc/nginx/sites-available/as-prescribed
ln -s /etc/nginx/sites-available/as-prescribed /etc/nginx/sites-enabled/as-prescribed
nginx -t && systemctl reload nginx
certbot --nginx -d asprescribed.sunrisesoftware.app
```

The certificate step needs the DNS record first.

## Update

```bash
cd /opt/as-prescribed/app && git pull --ff-only
UV_PYTHON_DOWNLOADS=never /opt/as-prescribed/uv/bin/uv sync --frozen --no-dev
systemctl restart as-prescribed
curl -fsS http://127.0.0.1:8300/health
```

Do not copy `nginx.conf` over the machine's file after certbot has run: the machine's copy carries
the certificate lines.
