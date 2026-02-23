# Base Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /code/
RUN pip install --upgrade pip && pip install -r base.txt

# Copy project
COPY . /code/

# Run entrypoint script
# COPY ./docker/entrypoint.sh /code/
# RUN chmod +x /code/entrypoint.sh
# ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
