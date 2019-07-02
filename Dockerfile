FROM python:3.7-alpine
ARG GIT_COMMIT
ENV GIT_COMMIT ${GIT_COMMIT}
WORKDIR /app
COPY bemani.conf main.py requirements.txt /app/
RUN pip install --trusted-host pypi.python.org --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "main.py"]
