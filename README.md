# Project Pulse

## Overview

Project Pulse is a backend API for managing and analyzing meeting notes. It uses an AI model hosted on Azure to generate summaries, action items, and potential risk.

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


python3 -m uvicorn main:app --reload --env-file .env

Open-http://127.0.0.1:8000/docs

Need three environmential variable
: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT