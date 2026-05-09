FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_PYTHON=/usr/local/bin/python3.11

WORKDIR /app
COPY backend/pyproject.toml ./backend/
RUN cd backend && echo "3.11" > .python-version && uv sync --no-dev --python /usr/local/bin/python3.11

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN cat > /etc/nginx/sites-available/default << 'NGINX'
server {
    listen 80;
    root /app/frontend/dist;
    index index.html;

    # Headers de seguranca
    add_header Content-Security-Policy "frame-ancestors 'self' https://inteia.com.br https://*.vercel.app" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # Ocultar versao do servidor
    server_tokens off;

    location / { try_files $uri $uri/ /index.html; }
    location /health/ {
        proxy_pass http://127.0.0.1:5001/health/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
    }
}
NGINX

RUN printf '#!/bin/bash\ncd /app/backend && uv run --python python3.11 python3.11 run.py &\nsleep 2\nnginx -g "daemon off;"\n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 80
CMD ["/app/start.sh"]
