FROM node:20-alpine

WORKDIR /app

# Allow legacy peer deps inside the build (testing libs conflict with React 19)
ENV NPM_CONFIG_LEGACY_PEER_DEPS=true

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]