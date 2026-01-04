# Development Dockerfile for Vite
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code (will be overridden by volume in docker-compose)
COPY . .

# Expose port
EXPOSE 5173

# Default command (will be overridden by docker-compose command)
CMD ["npm", "run", "dev"]
