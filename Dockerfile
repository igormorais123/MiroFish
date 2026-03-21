FROM python:3.12-slim

# Node.js + nginx + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gcc g++ make nginx \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Dependencias
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml ./backend/
RUN npm ci --prefix frontend
RUN cd backend && echo "3.12" > .python-version && uv sync --no-dev

# Codigo
COPY . .

# Build frontend para arquivos estaticos
RUN cd frontend && npm run build

# Nginx config: serve frontend + proxy /api para backend
RUN cat > /etc/nginx/sites-available/default << 'NGINX'
server {
    listen 80;
    root /app/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
    }
}
NGINX

# Script de startup
RUN cat > /app/start.sh << 'START'
#!/bin/bash
cd /app/backend && uv run python run.py &
sleep 2
nginx -g "daemon off;"
START
RUN chmod +x /app/start.sh

EXPOSE 80 5001

CMD ["/app/start.sh"]
