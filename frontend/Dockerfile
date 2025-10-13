
# Frontend Dockerfile for React client
# Multi-stage: build with Node, serve with Nginx

FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Allow overriding API URL at build time
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

RUN npm run build

FROM nginx:1.27-alpine AS runtime

# Copy nginx config as template
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf.template

# Copy custom entrypoint script
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy built React app
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.sh"]
