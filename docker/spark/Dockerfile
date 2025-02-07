FROM openjdk:11-slim

# Set environment variables
ENV SPARK_VERSION=3.2.0
ENV HADOOP_VERSION=3.2
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget python3 python3-pip procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install Spark
RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy entrypoint script
COPY docker/spark/entrypoint.sh /
RUN chmod +x /entrypoint.sh

WORKDIR $SPARK_HOME

# Expose Spark ports
EXPOSE 8080 7077 6066

ENTRYPOINT ["/entrypoint.sh"]
