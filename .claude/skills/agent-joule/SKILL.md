---
name: agent-joule
description: Generates the joule/ folder for an A2A+LangGraph agent project — DAS deployment descriptor, A2A capability, function, and scenario YAML files — from agent-intent.md. Run after agent-project-intent and agent-core when Joule integration is required.
---

# Agent Joule Generator

Reads `agent-intent.md` and generates the complete `joule/` folder for deploying the agent via SAP DAS (Joule).

**Prerequisite:** `agent-intent.md` must exist (run `agent-project-intent` first). Only run this skill if Joule integration is required per `agent-intent.md`.

---

## Instructions

### Step 1 — Read Intent

Read `agent-intent.md` and extract:
- `{{AGENT_NAME}}` — project folder name (kebab-case)
- `{{AGENT_TITLE}}` — human-readable title
- `{{AGENT_DESCRIPTION}}` — full description
- `{{AGENT_NAME_YAML}}` — snake_case name (used in YAML names)
- `{{SYSTEM_ALIAS}}` — SCREAMING_SNAKE alias (e.g. `WEATHER_AGENT`)
- `{{BTP_DESTINATION}}` — SCREAMING_SNAKE BTP destination name (e.g. `WEATHER_AGENT_SERVICE`)
- `{{SCENARIO_NAME}}` — snake_case scenario name (e.g. `weather_agent`)
- `{{FUNCTION_NAME}}` — `agent_` + SCENARIO_NAME (e.g. `agent_weather_agent`)
- `{{SCENARIO_DESCRIPTION}}` — one-sentence description of what the Joule scenario does

### Step 2 — Create Directories

```bash
mkdir -p {{AGENT_NAME}}/joule/a2a/functions
mkdir -p {{AGENT_NAME}}/joule/a2a/scenarios/{{SCENARIO_NAME}}
```

### Step 3 — Write All Files

Write every file below, substituting all `{{PLACEHOLDER}}` values. Do not skip any file.

---

## File: `{{AGENT_NAME}}/joule/da.sapdas.yaml`

```yaml
schema_version: 1.4.0
name: {{AGENT_NAME_YAML}}
capabilities:
  - type: local
    folder: ./a2a
```

---

## File: `{{AGENT_NAME}}/joule/a2a/capability.sapdas.yaml`

```yaml
schema_version: 3.27.0

metadata:
  display_name: {{AGENT_NAME_YAML}}
  namespace: com.sap.das.dev
  name: {{AGENT_NAME_YAML}}
  version: 1.0.0
  description: >-
    {{AGENT_DESCRIPTION}}

system_aliases:
  {{SYSTEM_ALIAS}}:
    destination: {{BTP_DESTINATION}}
```

---

## File: `{{AGENT_NAME}}/joule/a2a/capability_context.yaml`

```yaml
variables:
  - name: agent_context_id
```

---

## File: `{{AGENT_NAME}}/joule/a2a/functions/{{FUNCTION_NAME}}.yaml`

```yaml
parameters:
  - name: agent_context_id
    optional: true

action_groups:
  - actions:
    - type: agent-request
      agent_type: remote
      system_alias: {{SYSTEM_ALIAS}}
      result_variable: _agent_response

result:
  agent_response_message: <? _agent_response.body.message ?>
  agent_result: <? _agent_response ?>
  agent_context_id: <? _agent_response.body.contextId ?>
```

---

## File: `{{AGENT_NAME}}/joule/a2a/scenarios/{{SCENARIO_NAME}}/{{SCENARIO_NAME}}.yaml`

```yaml
description: >-
  {{SCENARIO_DESCRIPTION}}

target:
  type: function
  name: {{FUNCTION_NAME}}
  parameters:
    - name: agent_context_id
      value: $capability_context.agent_context_id

response_context:
  - description: Response from {{AGENT_TITLE}}
    value: $target_result.agent_result

capability_context:
  - name: agent_context_id
    value: $target_result.agent_context_id
```

---

## File: `{{AGENT_NAME}}/joule/.env.example`

```
# Joule CLI credentials — obtained from SAP BTP service key
JOULE_AUTH_URL=https://<subaccount>.authentication.<region>.hana.ondemand.com
JOULE_CLIENT_ID=sb-...!b<number>
JOULE_CLIENT_SECRET=<secret>
JOULE_DEFAULT_IDP=false
```

---

## File: `{{AGENT_NAME}}/joule/README.md`

```markdown
# {{AGENT_TITLE}} — Joule Deployment

Deploy this agent to Joule (SAP DAS) so it can be invoked from the Joule UI.

## Prerequisites

- [Joule CLI](https://help.sap.com/docs/joule) installed and on your PATH
- BTP destination **`{{BTP_DESTINATION}}`** created, pointing to your running agent URL
- Joule service key credentials

## Setup

1. Copy `.env.example` to `.env` and fill in your Joule credentials:
   ```bash
   cp .env.example .env
   ```

2. Log in to Joule:
   ```bash
   joule login --use-env .env --sso-passcode
   ```

3. Validate the YAML files:
   ```bash
   cd a2a && joule compile
   ```

4. Deploy:
   ```bash
   cd ..
   joule deploy da.sapdas.yaml
   ```

5. Open in Joule UI:
   ```bash
   joule launch {{AGENT_NAME_YAML}}
   ```

## BTP Destination

Create a BTP destination named **`{{BTP_DESTINATION}}`** with:

| Field | Value |
|---|---|
| Name | `{{BTP_DESTINATION}}` |
| Type | HTTP |
| URL | Your agent URL (e.g. `https://your-ngrok-url.ngrok-free.app`) |
| Authentication | NoAuthentication |

For local development, expose with ngrok:
```bash
ngrok http {{PORT}} --host-header="localhost:{{PORT}}"
```
Then update the destination URL to the ngrok HTTPS URL.

## Architecture

```
Joule UI
  └── Scenario: {{SCENARIO_NAME}}
        └── Function: {{FUNCTION_NAME}}
              └── A2A request → {{SYSTEM_ALIAS}} alias
                    └── BTP Destination: {{BTP_DESTINATION}}
                          └── Agent: http://localhost:{{PORT}}/
```
```

---

## Step 4 — Confirm

Print a summary of what was created:

```
Created:
  {{AGENT_NAME}}/joule/da.sapdas.yaml
  {{AGENT_NAME}}/joule/.env.example
  {{AGENT_NAME}}/joule/README.md
  {{AGENT_NAME}}/joule/a2a/capability.sapdas.yaml
  {{AGENT_NAME}}/joule/a2a/capability_context.yaml
  {{AGENT_NAME}}/joule/a2a/functions/{{FUNCTION_NAME}}.yaml
  {{AGENT_NAME}}/joule/a2a/scenarios/{{SCENARIO_NAME}}/{{SCENARIO_NAME}}.yaml
```

Then tell the user the remaining setup steps:
1. Create BTP destination **`{{BTP_DESTINATION}}`** pointing to the running agent URL.
2. Fill in `joule/.env` with Joule CLI credentials.
3. Run `joule login --use-env joule/.env --sso-passcode`.
4. Run `cd joule/a2a && joule compile` to validate YAML.
5. Run `cd joule && joule deploy da.sapdas.yaml` to deploy.

---

## Reference: Key File Roles

| File | Purpose |
|---|---|
| `da.sapdas.yaml` | Root deployment descriptor — names the deployment and points to `./a2a` |
| `capability.sapdas.yaml` | Capability metadata + system alias mapping alias → BTP destination |
| `capability_context.yaml` | Declares `agent_context_id` — carries thread state across turns |
| `functions/{{FUNCTION_NAME}}.yaml` | A2A function — makes the agent-request and maps response fields |
| `scenarios/{{SCENARIO_NAME}}/{{SCENARIO_NAME}}.yaml` | Joule routing — describes when to invoke the function and how to pass context |

## Reference: Naming Conventions

| Field | Format | Example |
|---|---|---|
| `AGENT_NAME_YAML` | snake_case | `weather_agent` |
| `SYSTEM_ALIAS` | SCREAMING_SNAKE | `WEATHER_AGENT` |
| `BTP_DESTINATION` | SCREAMING_SNAKE | `WEATHER_AGENT_SERVICE` |
| `FUNCTION_NAME` | `agent_` + snake_case | `agent_weather_agent` |
| `SCENARIO_NAME` | snake_case | `weather_agent` |
| Folder names | snake_case | `scenarios/weather_agent/` |
