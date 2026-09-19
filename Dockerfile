# Multi-stage: pygbag (WASM) → nginx. Runtime CDN is vendored (same-origin).
#
#   docker build -t lena2:latest .
#   docker tag lena2:latest YOUR_REGISTRY/lena2:1.0.0
#   docker push YOUR_REGISTRY/lena2:1.0.0

FROM python:3.12-bookworm AS build

WORKDIR /work
RUN pip install --no-cache-dir "pygbag==0.9.3"

COPY main.py game.py gfx.py levels.py settings.py ui.py favicon.png /work/game/
COPY docker/default.tmpl /work/default.tmpl

# Same-origin CDN path — no pygame-web.github.io in the browser
RUN python -m pygbag \
    --build \
    --app_name lena2 \
    --package org.bch.lena2 \
    --title "Поезд БЧ" \
    --template /work/default.tmpl \
    --icon /work/game/favicon.png \
    --cdn /cdn/0.9.3/ \
    --ume_block 1 \
    /work/game

FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /work/game/build/web /usr/share/nginx/html
COPY docker/browserfs.min.js /usr/share/nginx/html/browserfs.min.js
COPY docker/cdn/ /usr/share/nginx/html/cdn/

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
