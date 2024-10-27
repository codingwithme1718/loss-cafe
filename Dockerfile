FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "loss_cafe.wsgi:application"]
