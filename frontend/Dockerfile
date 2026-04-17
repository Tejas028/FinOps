FROM node:20-slim

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

# Pass VITE API URL at build time if needed
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
