FROM python:3-alpine AS patcher
COPY patch-jar.py /tmp/patch-jar.py
COPY --from=christiand9699/gateway-iam:latest-dev-mario /app.jar /app.jar
RUN python3 /tmp/patch-jar.py /app.jar

FROM christiand9699/gateway-iam:latest-dev-mario
COPY --from=patcher /app.jar /app.jar
