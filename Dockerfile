FROM python:3.12-slim

# Install GDAL dependencies
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to help Python find GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install GDAL via pip
RUN GDAL_VERSION=$(gdal-config --version) && \
    pip install GDAL==$GDAL_VERSION

# Install gunicorn
RUN pip install gunicorn

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install pandarus_remote package
RUN pip install .
