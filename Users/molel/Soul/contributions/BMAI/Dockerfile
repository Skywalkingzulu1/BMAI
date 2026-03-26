# Use the lightweight Nginx image
FROM nginx:alpine

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Copy website assets
COPY index.html /usr/share/nginx/html/

# Expose HTTP port
EXPOSE 80

# Health‑check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --spider http://localhost/health || exit 1

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]