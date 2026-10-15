FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system agentmail && adduser --system --ingroup agentmail agentmail
WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

USER agentmail
EXPOSE 8765

CMD ["agent-team-mail", "--transport", "http"]
