#!/bin/sh
set -e

# Heroku provides a $PORT environment variable
# We need to substitute it in the nginx config
if [ -n "$PORT" ]; then
  # Use envsubst to replace $PORT in the nginx config
  envsubst '$PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
fi

# Start nginx
exec nginx -g 'daemon off;'
