FROM jupyter/pyspark-notebook:spark-3.2.0

USER root

# Install additional system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install project requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install additional Jupyter extensions
RUN pip install --no-cache-dir \
    jupyter_contrib_nbextensions \
    jupyter_nbextensions_configurator \
    jupyterlab

# Enable Jupyter extensions
RUN jupyter contrib nbextension install --system && \
    jupyter nbextensions_configurator enable --system

# Create directories for mounting
RUN mkdir -p /data /home/jovyan/work && \
    fix-permissions /data && \
    fix-permissions /home/jovyan/work

# Install example notebook dependencies
RUN pip install --no-cache-dir \
    pandas \
    matplotlib \
    seaborn \
    scikit-learn \
    torch \
    torchvision \
    Pillow \
    requests

# Switch back to jovyan user
USER jovyan

# Set up Jupyter configuration
COPY docker/jupyter/jupyter_notebook_config.py /home/jovyan/.jupyter/
RUN jupyter notebook --generate-config && \
    echo "c.NotebookApp.token = ''" >> /home/jovyan/.jupyter/jupyter_notebook_config.py

WORKDIR /home/jovyan/work

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
