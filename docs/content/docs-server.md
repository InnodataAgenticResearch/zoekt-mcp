---
title: "Running the docs server"
sidebar_position: 4
---

This site is Docusaurus 3 in `docs/`. Hand-written pages live in `docs/content/`.

## Serve the built site

```bash
just docs-serve            # = nix run .#docs-serve
PORT=3001 just docs-serve  # another port
```

- **Builds** the site with Nix from pinned npm dependencies (offline, the same build CI checks).
- **Serves** it with a static file server on <http://127.0.0.1:3000> (localhost only).
- **Stop** with Ctrl-C.

## Live-reload while writing

```bash
just docs-dev   # npm ci (first run), then docusaurus start on 127.0.0.1:3000
```

Stop with Ctrl-C.

## From your laptop

The server only listens on the VM's loopback interface. Tunnel to it over SSH:

```bash
gcloud compute ssh <vm> -- -L 3000:localhost:3000
```

Then open <http://localhost:3000> on your laptop. Ctrl-C ends the tunnel.
