FROM python:3.12-slim 


# Install curl and uv
RUN apt-get update && apt-get install -y curl ca-certificates && \
    update-ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*


# Add uv to PATH
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# Set working directory 
WORKDIR /URL_Shortener 

# Copy everything into container 

COPY . . 

# Install dependencies using uv
RUN uv sync --frozen 

# Make script executable
RUN chmod +x ./entrypoint.sh

# Expose FastAPI port 

EXPOSE 8000 

# Set entrypoint first, CMD second
ENTRYPOINT ["./entrypoint.sh"]

# Start FastAPI app using uvicorn 

CMD ["uv", "run", "fastapi", "run", "--app", "app", "--host", "0.0.0.0", "--port", "8000"]