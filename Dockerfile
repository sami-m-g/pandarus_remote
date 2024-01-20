# Start from the latest LTS version of Ubuntu
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies for Conda
RUN apt-get update && apt-get install -y wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p /miniconda && \
    rm /miniconda.sh

# Add Conda to PATH
ENV PATH="/miniconda/bin:${PATH}"

# Copy your environment.yml file (assumes it's in the same directory as the Dockerfile)
COPY environment.yml /app/environment.yml

# Set the working directory in the container
WORKDIR /app

# Create the Conda environment
RUN conda env create -f environment.yml

# Activate the Conda environment
SHELL ["conda", "run", "-n", "pandarus_remote", "/bin/bash", "-c"]

# Copy the current directory contents into the container at /app
COPY . /app

# Make port available to the world outside this container
EXPOSE 80

# Define the command to run your application
CMD ["conda", "run", "-n", "pandarus_remote", "python", "app.py"]
