# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the processing script into the container
COPY process_trial_data.py .

# Run the processing script when the container launches
# You can override the CMD arguments when running the container to pass a dynamically mounted volume
CMD ["python", "process_trial_data.py", "--base_dir", "/data"]
