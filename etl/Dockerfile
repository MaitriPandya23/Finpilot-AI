FROM python:3.11-slim

# Install OpenJDK for PySpark
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Hadoop AWS & AWS SDK jars for Spark S3A connectivity
RUN mkdir -p /opt/spark/jars && \
    curl -sS https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar -o /opt/spark/jars/hadoop-aws-3.3.4.jar || true && \
    curl -sS https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar || true

COPY spark_etl.py .

ENTRYPOINT ["python", "spark_etl.py"]
