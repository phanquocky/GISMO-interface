# Use Ubuntu as the base image
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install Python + pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get install -y git && \
    apt-get install -y cmake build-essential &&\
    rm -rf /var/lib/apt/lists/*

RUN apt update && \
    apt install -y build-essential cmake git python3-dev libboost-program-options-dev libm4ri-dev

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt
RUN export LD_LIBRARY_PATH=/app/cadiback:$LD_LIBRARY_PATH

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose Flask port
EXPOSE 5000


# Declare volume (for persistence)
VOLUME ["/app"]

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV PROJECT_DIR=/app/identifying-codes
ENV PBLIB_DIR=/app/pblib/build

ENTRYPOINT ["/app/entrypoint.sh"]
# Command to run Flask
CMD ["flask", "run", "--reload"]
