FROM python:3.11

# Instala o Node.js (>=18) e as ferramentas necessarias
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copia o uv da imagem oficial
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copia primeiro os manifests de dependencia para aproveitar cache
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Instala dependencias de Node e Python
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Copia o codigo-fonte do projeto
COPY . .

EXPOSE 3000 5001

# Inicia frontend e backend juntos em modo de desenvolvimento
CMD ["npm", "run", "dev"]
