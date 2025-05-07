# Use a lightweight Nginx image
FROM nginx:alpine

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the frontend application files into the Nginx webroot
COPY . /usr/share/nginx/html

# Nginx listens on port 80 by default, which is exposed by the image
EXPOSE 80

# Command to run Nginx (default command of the base image)
CMD ["nginx", "-g", "daemon off;"]
