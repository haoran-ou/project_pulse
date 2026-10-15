# Project Pulse

## Overview

Project Pulse is a backend API for managing and analyzing meeting notes. It uses an AI model hosted on Azure to generate summaries, action items, and potential risks.

## Current Features

- Create, view, update, and delete meeting records.
- Store meeting records in SQLite.
- Use AI to generate summaries, action items, and potential risks.
- Analyze stored meetings by ID.
- Save analysis results and source-text snapshots in SQLite.
- Retrieve multiple analysis records for a meeting.
- Preserve saved records across server restarts.

## Current Limitations


- No dedicated end-user interface yet.
- AI analysis requires a configured Azure model deployment and API key.
- AI-generated content may be inaccurate; extraction quality is still being evaluated.
- Cross-meeting project progress tracking is not implemented yet.
- Local model inference and desktop/mobile installers are planned but not implemented.

## Running Locally

Developed with Python 3.12.

### 1. Clone the repository

```bash
git clone git@github.com:haoran-ou/project_pulse.git
cd project_pulse
```

The SSH command requires GitHub SSH access to be configured.

### 2. Create a virtual environment and install dependencies

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Configure Azure AI

Create a local `.env` file using `.env.example` as a template.
If `.env` already exists, keep your existing configuration.

Replace the placeholder values with your own Azure API key,
endpoint, and deployment name. AI analysis requires an accessible
Azure model deployment and may incur usage charges.

Never commit `.env` or real API keys.

### 4. Start the server

Run from the repository root:

```bash
python -m uvicorn main:app --reload --env-file .env
```

Open http://127.0.0.1:8000/docs to explore the API.
Press Ctrl+C in the terminal to stop the server.

## Running Tests

With the virtual environment activated, run:

```bash
python -m unittest discover -s tests -v
```