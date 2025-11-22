FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Expose the Dash port
EXPOSE 7860

# Run the Dash app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:server"]
