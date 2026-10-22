FROM python:3-alpine AS patcher
COPY --from=christiand9699/frontend-react:latest-dev-mario /usr/share/nginx/html/ui/assets/ /tmp/assets/
COPY patch-js.py /tmp/patch-js.py
RUN JS_FILE=$(ls /tmp/assets/index-*.js | head -1) && \
  cp "$JS_FILE" /tmp/index.js && \
  python3 /tmp/patch-js.py /tmp/index.js && \
  sed -i \
    -e 's|https://dev.christiandellisanti.uk|http://100.87.231.127:8080|g' \
    -e 's|https://www.christiandellisanti.uk|http://100.87.231.127:8080|g' /tmp/index.js && \
  cp /tmp/index.js "$JS_FILE"

FROM christiand9699/frontend-react:latest-dev-mario
COPY --from=patcher /tmp/assets/ /usr/share/nginx/html/ui/assets/
