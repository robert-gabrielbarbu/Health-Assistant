# LinkedIn Capability — Joule Deployment

## Prerequisites

- Joule CLI installed
- SAP BTP destination `linkedin-agent` configured pointing to the LinkedIn A2A agent URL
- LinkedIn A2A agent running (see `../Agentic-AI-Zone/README.md`)

### Expose via ngrok (for Joule)

```bash
ngrok http 8000 --host-header="localhost:8000"
```

Copy the `https://....ngrok-free.app` URL — use it as the BTP destination URL for `STRAVA_COACH_AGENT`.

1. Create a BTP destination named `STRAVA_COACH_AGENT`:
   - **URL**: your ngrok URL
   - **Type**: HTTP
   - **Authentication**: NoAuthentication

2. Log in to Joule CLI and deploy the capability:

Check [Joule README](/joule/README.md)

## 1. Login to Joule CLI

Copy the environment file and fill in your credentials:

```bash
cp .env.example .env
```

Login using the custom IDP (do **not** select "Default Identity Provider"):

```bash
joule login --use-env .env --sso-passcode
```

## 2. Compile & Deploy Capability

Compile the design-time artifact from the `a2a/` directory:

```bash
cd a2a && joule compile
```

Deploy the assistant (run from `joule/`):

```bash
joule deploy ../da.sapdas.yaml
```

> Use `-n <your-assistant-name>` to override the assistant name.

## 3. Open Joule

```bash
joule launch strava_coach_agent
```

You can now trigger the Strava coach by sending a message such as:

> "Create my training plan for today"
