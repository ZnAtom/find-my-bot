FROM python:3.12-slim

RUN apt-get update && apt-get install -y postgresql-client openssl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 使用国内 PyPI 镜像，避免连接官方源时 SSL 中断
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
# 先装 CPU 版 torch + torchvision（必须成对，同源同版本，否则 torchvision::nms 算子缺失）
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]
