FROM node:18-alpine

WORKDIR /app

COPY payment-api/package*.json ./
RUN npm install --omit=dev

COPY payment-api/ ./

EXPOSE 3001

CMD ["node", "server.js"]
