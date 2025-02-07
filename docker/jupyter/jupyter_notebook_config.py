c = get_config()

# Allow all IP addresses to connect
c.NotebookApp.ip = '0.0.0.0'

# Don't open browser automatically
c.NotebookApp.open_browser = False

# No authentication required - only for development
c.NotebookApp.token = ''
c.NotebookApp.password = ''

# Allow root access
c.NotebookApp.allow_root = True

# Set the notebook directory
c.NotebookApp.notebook_dir = '/home/jovyan/work'

# Enable all extensions
c.NotebookApp.nbserver_extensions = {}
c.NotebookApp.nbserver_extensions.update({
    'jupyter_nbextensions_configurator': True
})

# Set up logging
c.NotebookApp.log_level = 'INFO'
