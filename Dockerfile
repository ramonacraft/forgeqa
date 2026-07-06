# ForgeQA app image. Ships the Playwright browsers so generated tests can run
# inside the container later. Based on the official Playwright Python image.
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Run the dashboard. Customers hit http://localhost:8501
CMD ["streamlit", "run", "app/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
