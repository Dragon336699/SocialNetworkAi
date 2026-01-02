FROM python:3.10-slim

WORKDIR /app

# 1. Cài dependency cơ bản
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2. Add Microsoft repo (CÁCH MỚI – KHÔNG dùng apt-key)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | tee /usr/share/keyrings/microsoft-prod.gpg > /dev/null

RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
    https://packages.microsoft.com/debian/11/prod bullseye main" \
    > /etc/apt/sources.list.d/mssql-release.list

# 3. Cài ODBC Driver 18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# 4. Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. App source
COPY . .

EXPOSE 8000
CMD ["uvicorn", "Main:app", "--host", "0.0.0.0", "--port", "8000"]
