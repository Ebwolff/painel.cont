FROM node:20-alpine AS builder

WORKDIR /app

# Copiar os arquivos de dependência
COPY package*.json ./

# Instalar TODAS as dependências (incluindo devDependencies para build)
RUN npm install

# Copiar o código fonte
COPY . .

# Fazer o Build
RUN npm run build

# --- Container de Produção ---
FROM node:20-alpine

WORKDIR /app

# Copiar apenas os arquivos necessários para produção do container anterior
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist

# Variáveis de Ambiente necessárias
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

# Comando de boot
CMD ["npm", "run", "start:prod"]
