FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

# For dev, but production serve static or use nginx
CMD ["npm", "run", "dev"]
