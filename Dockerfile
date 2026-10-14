# PiriMU — เว็บ pirimu.com + ไฟล์ดาวน์โหลด + หน้า admin ในคอนเทนเนอร์เดียว
# Coolify: Build Pack = Dockerfile, Port = 80, Persistent Storage = /data, Env = ADMIN_PASSWORD

# ---------- 1) แพ็กไฟล์ดาวน์โหลด + สร้าง version.json อัตโนมัติ ----------
FROM alpine:3.20 AS build
RUN apk add --no-cache zip
WORKDIR /src
COPY browser/ browser/
COPY web/ web/
RUN set -eu; \
    VER="$(sed -n 's/^APP_VERSION = "\(.*\)"/\1/p' browser/pirimu.py)"; \
    test -n "$VER"; \
    mkdir -p out/downloads pkg/PiriMU-Windows pkg/PiriMU-Mac; \
    cp -r web/. out/; \
    sed -i 's/\r$//' out/install.sh; \
    for d in PiriMU-Windows PiriMU-Mac; do \
      cp browser/pirimu.py browser/requirements.txt browser/icon.png pkg/$d/; \
    done; \
    cp browser/icon.ico browser/windows/* pkg/PiriMU-Windows/; \
    cp browser/mac/* pkg/PiriMU-Mac/; \
    for f in pkg/PiriMU-Windows/*.bat pkg/PiriMU-Windows/*.txt; do sed -i 's/\r$//; s/$/\r/' "$f"; done; \
    sed -i 's/\r$//' pkg/PiriMU-Mac/*.command; \
    chmod 755 pkg/PiriMU-Mac/*.command; \
    cd pkg && zip -qrX ../out/downloads/PiriMU-Windows.zip PiriMU-Windows && zip -qrX ../out/downloads/PiriMU-Mac.zip PiriMU-Mac && cd ..; \
    printf '{"version":"%s","url":"https://pirimu.com/#download","note":"ดูรายละเอียดที่ pirimu.com"}\n' "$VER" > out/version.json; \
    echo "PiriMU version $VER packaged"

# ---------- 2) เซิร์ฟเวอร์ (Flask) : เว็บ + ดาวน์โหลด + สถิติ + หน้า admin ----------
FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server/app.py .
COPY --from=build /src/out /app/static
ENV STATIC_DIR=/app/static DATA_DIR=/data PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1/healthz')" || exit 1
CMD ["gunicorn", "-w", "2", "--threads", "4", "-b", "0.0.0.0:80", "app:app"]
