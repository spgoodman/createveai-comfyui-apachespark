#!/bin/bash

# Exit on error
set -e

if [ "$SPARK_MODE" = "master" ]; then
    echo "Starting Spark master node..."
    # Start master
    /opt/spark/sbin/start-master.sh -h spark
    
    # Keep container running
    tail -f /opt/spark/logs/spark--org.apache.spark.deploy.master.Master-1-*.out
elif [ "$SPARK_MODE" = "worker" ]; then
    echo "Starting Spark worker node..."
    # Start worker
    /opt/spark/sbin/start-worker.sh ${SPARK_MASTER_URL} \
        --memory ${SPARK_WORKER_MEMORY:-1G} \
        --cores ${SPARK_WORKER_CORES:-1}
    
    # Keep container running
    tail -f /opt/spark/logs/spark--org.apache.spark.deploy.worker.Worker-1-*.out
else
    echo "Invalid SPARK_MODE: $SPARK_MODE"
    echo "Must be either 'master' or 'worker'"
    exit 1
fi
