# Use a lightweight version of Python
FROM python:3.10-slim

# Install FFmpeg at the system level
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set our working directory inside the container
WORKDIR /app

# Copy our requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our worker script
COPY worker.py .

# Tell the container to run the script when it starts
# The -u flag ensures Python prints logs to Docker immediately
CMD ["python", "-u", "worker.py"]