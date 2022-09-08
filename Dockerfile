FROM python:3.10-alpine AS build
COPY requirements.txt .
RUN apk --no-cache add -t build-dep python3-dev build-base && \
    pip install --user --trusted-host pypi.python.org --no-cache-dir -r requirements.txt && \
    apk del build-dep

FROM python:3.10-alpine AS run
ARG GIT_COMMIT
ENV GIT_COMMIT ${GIT_COMMIT}
WORKDIR /app
COPY main.py /app/
COPY --from=build /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENTRYPOINT ["python", "main.py"]
