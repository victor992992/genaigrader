# Scripts Directory

This directory contains utility scripts for managing the Genaigrader project. These are only intended for use by developers and maintainers of the Genaigrader project. They are not intended for end-users or production environments. They assume that GenAI Grader is cloned in `$HOME/genaigrader`. They also assume that ngrok is installed and configured.

Below is a brief description of each script:

- **start_genaigrader.sh**: Shell script to start the Genaigrader application server.
- **stop_genaigrader.sh**: Shell script to stop the Genaigrader application server.

## Usage

Run the scripts from the project root using bash:

```bash
bash scripts/start_genaigrader.sh
bash scripts/stop_genaigrader.sh
```

Ensure you have the necessary permissions to execute these scripts. You may need to run:

```bash
chmod +x scripts/*.sh
```
