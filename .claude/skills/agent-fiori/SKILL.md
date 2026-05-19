---
name: agent-fiori
description: Generates the app/ folder — a complete SAPUI5 Fiori chat UI for an A2A+LangGraph agent — from agent-intent.md. Produces package.json, ui5.yaml, Component.js, manifest.json, Chat view/controller, A2AService, CSS, and i18n. Run after agent-project-intent when Fiori UI is required.
---

# Agent Fiori UI Generator

Reads `agent-intent.md` and generates a complete SAPUI5 Fiori chat application in `{{AGENT_NAME}}/app/`.

The UI connects to the A2A agent via a `ui5-middleware-simpleproxy` that proxies `/api/agent` → `http://localhost:{{PORT}}`, so agent and UI can run side by side during development.

**Prerequisite:** `agent-intent.md` must exist (run `agent-project-intent` first). Only run this skill if `Fiori UI: Required: yes` in `agent-intent.md`.

---

## Instructions

### Step 1 — Read Intent

Read `agent-intent.md` and extract:
- `{{AGENT_NAME}}` — project folder name (kebab-case)
- `{{AGENT_TITLE}}` — human-readable title (e.g. `Weather Agent`)
- `{{AGENT_DESCRIPTION}}` — one-sentence description
- `{{AGENT_CLASS_NAME}}` — PascalCase class name (e.g. `WeatherAgent`)
- `{{UI5_NAMESPACE}}` — UI5 module namespace (e.g. `com.weather.agent`)
- `{{PORT}}` — agent server port (e.g. `8080`)
- `{{FIORI_PORT}}` — Fiori dev server port (e.g. `8081`)

Derive:
- `{{UI5_PATH}}` = `{{UI5_NAMESPACE}}` with `.` replaced by `/` (e.g. `com/weather/agent`)
- `{{INPUT_PLACEHOLDER}}` = Write a short, helpful textarea placeholder for this agent's domain (e.g. for a weather agent: `Ask about the forecast, current conditions, or weekly outlook...`)

### Step 2 — Create Directories

```bash
mkdir -p {{AGENT_NAME}}/app/webapp/controller
mkdir -p {{AGENT_NAME}}/app/webapp/css
mkdir -p {{AGENT_NAME}}/app/webapp/i18n
mkdir -p {{AGENT_NAME}}/app/webapp/model
mkdir -p {{AGENT_NAME}}/app/webapp/service
mkdir -p {{AGENT_NAME}}/app/webapp/view
```

### Step 3 — Write All Files

Write every file below, substituting all `{{PLACEHOLDER}}` values. Do not skip any file.

---

## File: `{{AGENT_NAME}}/app/package.json`

```json
{
  "name": "{{AGENT_NAME}}-ui",
  "version": "1.0.0",
  "description": "SAP Fiori UI for {{AGENT_TITLE}} A2A Agent",
  "scripts": {
    "start": "ui5 serve --open index.html",
    "build": "ui5 build --all"
  },
  "devDependencies": {
    "@ui5/cli": "^3.11.1",
    "ui5-middleware-simpleproxy": "^3.7.0"
  }
}
```

---

## File: `{{AGENT_NAME}}/app/ui5.yaml`

```yaml
specVersion: "3.0"
metadata:
  name: {{UI5_NAMESPACE}}
type: application
framework:
  name: SAPUI5
  version: "1.120.18"
  libraries:
    - name: sap.m
    - name: sap.f
    - name: sap.ui.layout
    - name: sap.ui.core
    - name: themelib_sap_horizon
server:
  customMiddleware:
    - name: ui5-middleware-simpleproxy
      mountPath: /api/agent
      afterMiddleware: compression
      configuration:
        baseUri: "http://localhost:{{PORT}}"
        strictSSL: false
```

---

## File: `{{AGENT_NAME}}/app/webapp/index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{AGENT_TITLE}}</title>
  <script id="sap-ui-bootstrap"
    src="resources/sap-ui-core.js"
    data-sap-ui-theme="sap_horizon"
    data-sap-ui-resourceroots='{"{{UI5_NAMESPACE}}": "./"}'
    data-sap-ui-compatVersion="edge"
    data-sap-ui-async="true"
    data-sap-ui-frameOptions="allow"
    data-sap-ui-oninit="module:sap/ui/core/ComponentSupport">
  </script>
</head>
<body class="sapUiBody" id="content">
  <div data-sap-ui-component
    data-name="{{UI5_NAMESPACE}}"
    data-id="container"
    data-settings='{"id":"{{AGENT_CLASS_NAME}}"}'
    style="height:100%">
  </div>
</body>
</html>
```

---

## File: `{{AGENT_NAME}}/app/webapp/Component.js`

```javascript
sap.ui.define([
    "sap/ui/core/UIComponent",
    "sap/ui/Device",
    "{{UI5_PATH}}/model/models"
], function (UIComponent, Device, models) {
    "use strict";

    return UIComponent.extend("{{UI5_NAMESPACE}}.Component", {

        metadata: {
            manifest: "json"
        },

        init: function () {
            UIComponent.prototype.init.apply(this, arguments);

            this.setModel(models.createDeviceModel(), "device");
            this.setModel(models.createChatModel(), "chat");

            this.getRouter().initialize();
        }
    });
});
```

---

## File: `{{AGENT_NAME}}/app/webapp/manifest.json`

```json
{
  "_version": "1.65.0",
  "sap.app": {
    "id": "{{UI5_NAMESPACE}}",
    "type": "application",
    "i18n": "i18n/i18n.properties",
    "title": "{{appTitle}}",
    "description": "{{appDescription}}",
    "applicationVersion": { "version": "1.0.0" }
  },
  "sap.ui": {
    "technology": "UI5",
    "icons": {
      "icon": "sap-icon://ai"
    },
    "deviceTypes": {
      "desktop": true,
      "tablet": true,
      "phone": false
    }
  },
  "sap.ui5": {
    "rootView": {
      "viewName": "{{UI5_NAMESPACE}}.view.App",
      "type": "XML",
      "async": true,
      "id": "app"
    },
    "dependencies": {
      "minUI5Version": "1.120.0",
      "libs": {
        "sap.m":         { "lazy": false },
        "sap.f":         { "lazy": false },
        "sap.ui.layout": { "lazy": false },
        "sap.ui.core":   { "lazy": false }
      }
    },
    "resources": {
      "css": [
        { "uri": "css/style.css" }
      ]
    },
    "contentDensities": {
      "compact": true,
      "cozy": true
    },
    "models": {
      "i18n": {
        "type": "sap.ui.model.resource.ResourceModel",
        "settings": {
          "bundleName": "{{UI5_NAMESPACE}}.i18n.i18n"
        }
      }
    },
    "routing": {
      "config": {
        "routerClass": "sap.m.routing.Router",
        "viewType": "XML",
        "viewPath": "{{UI5_NAMESPACE}}.view",
        "controlId": "appNav",
        "controlAggregation": "pages",
        "async": true
      },
      "routes": [
        {
          "pattern": "",
          "name": "chat",
          "target": "chat"
        }
      ],
      "targets": {
        "chat": {
          "viewName": "Chat",
          "viewLevel": 1
        }
      }
    }
  }
}
```

---

## File: `{{AGENT_NAME}}/app/webapp/model/models.js`

```javascript
sap.ui.define([
    "sap/ui/model/json/JSONModel",
    "sap/ui/Device"
], function (JSONModel, Device) {
    "use strict";

    return {
        createDeviceModel: function () {
            const oModel = new JSONModel(Device);
            oModel.setDefaultBindingMode("OneWay");
            return oModel;
        },

        createChatModel: function () {
            return new JSONModel({
                messages: [],
                contextId: null,
                isLoading: false,
                statusMessage: "",
                agentStatus: "Offline",
                agentUrl: "/api/agent",
                agentCard: {
                    name: "",
                    description: "",
                    skills: []
                }
            });
        }
    };
});
```

---

## File: `{{AGENT_NAME}}/app/webapp/service/A2AService.js`

Copy verbatim — no placeholders needed. This file is fully generic.

```javascript
/**
 * A2AService — JSON-RPC 2.0 client for the A2A agent.
 * Requests are routed through ui5-middleware-simpleproxy at /api/agent.
 */
sap.ui.define([], function () {
    "use strict";

    const AGENT_BASE = "/api/agent";

    function _rpcId() {
        return "rpc-" + Date.now() + "-" + Math.floor(Math.random() * 10000);
    }

    function _msgId() {
        return "msg-" + Date.now() + "-" + Math.floor(Math.random() * 10000);
    }

    function _extractText(task) {
        if (task.artifacts && task.artifacts.length > 0) {
            for (const artifact of task.artifacts) {
                for (const part of (artifact.parts || [])) {
                    if (part.kind === "text" && part.text) {
                        return part.text;
                    }
                }
            }
        }
        const msg = task.status && task.status.message;
        if (msg && msg.parts) {
            for (const part of msg.parts) {
                if (part.kind === "text" && part.text) return part.text;
            }
        }
        return "";
    }

    const A2AService = {

        getAgentCard: async function () {
            const resp = await fetch(AGENT_BASE + "/.well-known/agent.json");
            if (!resp.ok) throw new Error("Agent card request failed: " + resp.status);
            return resp.json();
        },

        sendMessage: async function (text, contextId) {
            const params = {
                message: {
                    kind: "message",
                    messageId: _msgId(),
                    role: "user",
                    parts: [{ kind: "text", text: text }]
                },
                configuration: { blocking: true }
            };
            if (contextId) {
                params.message.contextId = contextId;
            }

            const body = JSON.stringify({
                jsonrpc: "2.0",
                id: _rpcId(),
                method: "message/send",
                params: params
            });

            const resp = await fetch(AGENT_BASE + "/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: body
            });

            if (!resp.ok) {
                const errText = await resp.text().catch(() => resp.statusText);
                throw new Error("Agent request failed (" + resp.status + "): " + errText);
            }

            const data = await resp.json();

            if (data.error) {
                throw new Error("[A2A error " + data.error.code + "] " + data.error.message);
            }

            const task = data.result;
            return {
                text: _extractText(task),
                contextId: task.contextId || contextId || "",
                taskId: task.id || ""
            };
        },

        streamMessage: async function (text, contextId, onChunk) {
            const params = {
                message: {
                    kind: "message",
                    messageId: _msgId(),
                    role: "user",
                    parts: [{ kind: "text", text: text }]
                }
            };
            if (contextId) params.message.contextId = contextId;

            const body = JSON.stringify({
                jsonrpc: "2.0",
                id: _rpcId(),
                method: "message/stream",
                params: params
            });

            let resp;
            try {
                resp = await fetch(AGENT_BASE + "/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    },
                    body: body
                });
            } catch (e) {
                const result = await this.sendMessage(text, contextId);
                onChunk(result.text, true, result.contextId);
                return { contextId: result.contextId };
            }

            const contentType = resp.headers.get("content-type") || "";
            if (!resp.ok || !resp.body || !contentType.includes("text/event-stream")) {
                const result = await this.sendMessage(text, contextId);
                onChunk(result.text, true, result.contextId);
                return { contextId: result.contextId };
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let finalContextId = contextId || "";
            let isDoneFired = false;
            let lastArtifactText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split("\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith("data:")) continue;
                    const raw = line.slice(5).trim();
                    if (!raw || raw === "[DONE]") continue;
                    try {
                        const event = JSON.parse(raw);
                        const result = event.result;
                        if (!result) continue;

                        if (result.contextId) finalContextId = result.contextId;

                        if (result.status && result.status.state === "working") {
                            const statusText = _extractText({ status: result.status });
                            if (statusText) onChunk(statusText, false, finalContextId);
                        }

                        if (result.artifact) {
                            const text2 = _extractText({ artifacts: [result.artifact] });
                            if (text2) {
                                lastArtifactText = text2;
                                if (result.artifact.lastChunk === true) {
                                    isDoneFired = true;
                                    onChunk(text2, true, finalContextId);
                                } else {
                                    onChunk(text2, false, finalContextId);
                                }
                            }
                        }

                        if (result.status && result.status.state === "completed" && !isDoneFired) {
                            const text2 = _extractText(result) || lastArtifactText;
                            isDoneFired = true;
                            onChunk(text2, true, finalContextId);
                        }
                    } catch (_) {
                        // malformed event — skip
                    }
                }
            }

            if (!isDoneFired) {
                const result2 = await this.sendMessage(text, contextId);
                onChunk(result2.text, true, result2.contextId);
                return { contextId: result2.contextId };
            }

            return { contextId: finalContextId };
        }
    };

    return A2AService;
});
```

---

## File: `{{AGENT_NAME}}/app/webapp/controller/App.controller.js`

```javascript
sap.ui.define([
    "sap/ui/core/mvc/Controller"
], function (Controller) {
    "use strict";

    return Controller.extend("{{UI5_NAMESPACE}}.controller.App", {
        onInit: function () {
            if (sap.ui.Device.system.desktop) {
                this.getView().addStyleClass("sapUiSizeCompact");
            }
        }
    });
});
```

---

## File: `{{AGENT_NAME}}/app/webapp/controller/Chat.controller.js`

```javascript
sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "{{UI5_PATH}}/service/A2AService"
], function (Controller, MessageToast, MessageBox, A2AService) {
    "use strict";

    function _mdToHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/_(.+?)_/g, "<em>$1</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/^---$/gm, "<hr/>")
            .replace(/^[\-\*] (.+)$/gm, "<li>$1</li>")
            .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
            .replace(/^### (.+)$/gm, "<h4>$1</h4>")
            .replace(/^## (.+)$/gm, "<h3>$1</h3>")
            .replace(/^# (.+)$/gm, "<h2>$1</h2>")
            .replace(/\n/g, "<br/>");
    }

    return Controller.extend("{{UI5_NAMESPACE}}.controller.Chat", {

        onInit: function () {
            this._loadAgentCard();
        },

        _loadAgentCard: function () {
            const oModel = this._chatModel();
            A2AService.getAgentCard()
                .then(function (card) {
                    oModel.setProperty("/agentCard", card);
                    oModel.setProperty("/agentStatus", "Online");
                })
                .catch(function () {
                    oModel.setProperty("/agentStatus", "Offline");
                });
        },

        onLoadAgentCard: function () {
            this._loadAgentCard();
            MessageToast.show(this._i18n("msgRefreshingAgent"));
        },

        onNewThread: function () {
            const oModel = this._chatModel();
            oModel.setProperty("/contextId", null);
            oModel.setProperty("/messages", []);
            oModel.setProperty("/statusMessage", "");
            MessageToast.show(this._i18n("msgNewThread"));
        },

        onSend: function () {
            const oInput = this.byId("userInput");
            const sText = (oInput.getValue() || "").trim();
            if (!sText) return;

            oInput.setValue("");

            const oModel = this._chatModel();
            const sContextId = oModel.getProperty("/contextId");

            this._appendMessage("user", sText);
            oModel.setProperty("/isLoading", true);
            oModel.setProperty("/statusMessage", this._i18n("msgWorking"));

            const that = this;

            A2AService.streamMessage(sText, sContextId || undefined,
                function (chunkText, isDone, newContextId) {
                    if (isDone) {
                        oModel.setProperty("/isLoading", false);
                        oModel.setProperty("/statusMessage", "");
                        if (newContextId) oModel.setProperty("/contextId", newContextId);
                        that._appendMessage("agent", chunkText);
                        that._scrollToBottom();
                    } else {
                        oModel.setProperty("/statusMessage", chunkText || that._i18n("msgWorking"));
                    }
                }
            ).catch(function (err) {
                oModel.setProperty("/isLoading", false);
                oModel.setProperty("/statusMessage", "");
                MessageBox.error(err.message || that._i18n("msgError"));
            });

            this._scrollToBottom();
        },

        onClearInput: function () {
            this.byId("userInput").setValue("");
        },

        _appendMessage: function (sRole, sText) {
            const oModel = this._chatModel();
            const aMessages = oModel.getProperty("/messages") || [];
            aMessages.push({
                role: sRole,
                content: sText,
                contentHtml: _mdToHtml(sText)
            });
            oModel.setProperty("/messages", aMessages);
        },

        _scrollToBottom: function () {
            const oDomRef = this.byId("chatArea").getDomRef();
            if (!oDomRef) return;
            setTimeout(function () {
                oDomRef.scrollTop = oDomRef.scrollHeight;
            }, 200);
        },

        _chatModel: function () {
            return this.getOwnerComponent().getModel("chat");
        },

        _i18n: function (sKey) {
            return this.getOwnerComponent().getModel("i18n")
                .getResourceBundle().getText(sKey);
        }
    });
});
```

---

## File: `{{AGENT_NAME}}/app/webapp/view/App.view.xml`

```xml
<mvc:View
    controllerName="{{UI5_NAMESPACE}}.controller.App"
    xmlns:mvc="sap.ui.core.mvc"
    xmlns="sap.m"
    displayBlock="true">
    <Shell>
        <App id="appNav"/>
    </Shell>
</mvc:View>
```

---

## File: `{{AGENT_NAME}}/app/webapp/view/Chat.view.xml`

```xml
<mvc:View
    controllerName="{{UI5_NAMESPACE}}.controller.Chat"
    displayBlock="true"
    xmlns="sap.m"
    xmlns:l="sap.ui.layout"
    xmlns:core="sap.ui.core"
    xmlns:f="sap.f"
    xmlns:mvc="sap.ui.core.mvc">

    <Page class="coachPage" showHeader="false" enableScrolling="false">
        <content>
            <f:Card
                height="100%"
                class="coachCard sapUiTinyMarginTopBottom">
                <f:content>
                    <VBox
                        width="100%"
                        height="100%"
                        fitContainer="true"
                        class="coachVBox">

                        <!-- Header toolbar -->
                        <Toolbar height="4rem">
                            <core:Icon size="1.5rem" src="sap-icon://ai"/>
                            <Title
                                text="{i18n>appTitle}"
                                titleStyle="H5"
                                class="sapUiSmallMarginBegin"/>
                            <ToolbarSpacer/>
                            <ObjectStatus
                                text="{chat>/agentStatus}"
                                state="{= ${chat>/agentStatus} === 'Online' ? 'Success' : 'Error' }"
                                icon="sap-icon://connected"/>
                            <Button
                                icon="sap-icon://create-session"
                                tooltip="{i18n>btnNewThread}"
                                press=".onNewThread"/>
                            <Button
                                icon="sap-icon://refresh"
                                tooltip="{i18n>btnLoadAgentCard}"
                                press=".onLoadAgentCard"/>
                        </Toolbar>

                        <!-- Chat message list -->
                        <VBox
                            id="chatArea"
                            width="100%"
                            class="coachScroll">
                            <layoutData>
                                <FlexItemData growFactor="1"/>
                            </layoutData>
                            <List
                                id="messageList"
                                showSeparators="None"
                                showNoData="true"
                                noDataText="{i18n>noMessages}"
                                items="{chat>/messages}">
                                <CustomListItem type="Inactive">
                                    <!-- Agent message (left-aligned) -->
                                    <HBox
                                        visible="{= ${chat>role} === 'agent' }"
                                        class="sapThemePageBG chat-item-ai sapUiTinyMarginBegin sapUiLargeMarginEnd sapUiSmallMarginTopBottom">
                                        <VBox
                                            class="sapUiSmallMarginBegin sapUiSmallMarginTopBottom sapThemeText sapUiSmallMarginEnd"
                                            width="100%">
                                            <FormattedText
                                                htmlText="{chat>contentHtml}"
                                                class="sapUiTinyMarginBegin"/>
                                        </VBox>
                                    </HBox>

                                    <!-- User message (right-aligned) -->
                                    <HBox
                                        visible="{= ${chat>role} === 'user' }"
                                        class="chat-item-user sapUiTinyMarginEnd sapUiLargeMarginBegin sapUiSmallMarginTopBottom">
                                        <VBox class="sapUiSmallMarginBegin sapUiSmallMarginEnd sapUiSmallMarginTopBottom">
                                            <Text text="{chat>content}" textAlign="End"/>
                                        </VBox>
                                    </HBox>
                                </CustomListItem>
                            </List>
                        </VBox>

                        <!-- Working indicator -->
                        <MessageStrip
                            id="statusStrip"
                            text="{chat>/statusMessage}"
                            type="Information"
                            showIcon="true"
                            visible="{= !!${chat>/isLoading} }"/>

                        <!-- Input area -->
                        <HBox
                            justifyContent="Center"
                            class="sapUiTinyMargin"
                            id="inputContainer">
                            <VBox width="90%" id="inputBox">
                                <TextArea
                                    id="userInput"
                                    placeholder="{i18n>inputPlaceholder}"
                                    growing="true"
                                    growingMaxLines="5"
                                    class="cInput"
                                    enabled="{= !${chat>/isLoading} }">
                                    <layoutData>
                                        <FlexItemData growFactor="1" maxWidth="100%"/>
                                    </layoutData>
                                </TextArea>
                            </VBox>
                            <Button
                                id="clearButton"
                                class="cButton"
                                icon="sap-icon://decline"
                                type="Transparent"
                                press=".onClearInput"/>
                            <Button
                                id="sendBtn"
                                class="sButton"
                                icon="sap-icon://paper-plane"
                                type="Ghost"
                                press=".onSend"
                                enabled="{= !${chat>/isLoading} }"/>
                        </HBox>

                        <!-- Disclaimer -->
                        <HBox justifyContent="Center">
                            <VBox width="89%" alignContent="Start">
                                <MessageStrip
                                    text="{i18n>chatDisclaimer}"
                                    enableFormattedText="true"
                                    showIcon="true"
                                    showCloseButton="true"
                                    class="sapUiMediumMarginBottom"
                                    type="Warning"
                                    customIcon="sap-icon://high-priority"/>
                            </VBox>
                        </HBox>

                    </VBox>
                </f:content>
            </f:Card>
        </content>
    </Page>

</mvc:View>
```

---

## File: `{{AGENT_NAME}}/app/webapp/css/style.css`

Copy verbatim — no placeholders needed.

```css
/* ── Full-height chain ────────────────────────────────────────────────── */
.coachPage {
    height: 100vh;
}

.coachPage .sapMPageSection {
    height: 100%;
}

.coachCard.sapFCard {
    height: calc(100% - 1rem) !important;
    width: calc(100% - 4rem) !important;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.coachCard .sapFCardContent {
    flex: 1 1 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 0;
}

/* VBox fills card content as flex column */
.coachVBox.sapMFlexBox {
    flex: 1 1 0;
    min-height: 0;
    overflow: hidden;
}

/* Chat area: native CSS scroll */
.coachScroll.sapMFlexBox {
    flex: 1 1 0;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
}

/* ── Input area (absolute buttons over textarea) ─────────────────────── */

#inputContainer.sapMHBox {
    position: relative;
    flex-shrink: 0;
}

.cInput {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: calc(100% - 90px);
}

/* Unified border wrapping textarea + button area */
.cInput::before {
    content: "";
    position: absolute;
    top: -2px;
    right: -90px;
    bottom: -2px;
    left: -2px;
    border-radius: 0.5rem;
    border: 1px solid var(--sapField_BorderColor, #bfbfbf);
    pointer-events: none;
    z-index: 3;
}

.cInput:focus-within::before {
    border-color: var(--sapField_Hover_BorderColor);
}

.cInput .sapMTextAreaInner {
    border: none !important;
}

.sButton.sapMBtn {
    position: absolute;
    right: 0.9rem;
    top: 0.75rem;
    z-index: 4;
}

.cButton.sapMBtn {
    position: absolute;
    right: 3.3rem;
    top: 0.75rem;
    z-index: 4;
}

/* ── Chat bubbles ─────────────────────────────────────────────────────── */
.chat-item-ai {
    border-radius: 0rem 1rem 1rem 1rem;
    border-style: solid;
    border-width: thin;
    background-color: var(--sapContent_Illustrative_Color19);
}

.chat-item-user {
    border-radius: 1rem 0rem 1rem 1rem;
    border-style: solid;
    border-width: thin;
    background-color: var(--sapContent_Illustrative_Color6);
    margin-left: auto;
}
```

---

## File: `{{AGENT_NAME}}/app/webapp/i18n/i18n.properties`

```properties
# Application
appTitle={{AGENT_TITLE}}
appDescription={{AGENT_DESCRIPTION}}

# Chat
noMessages=Start a conversation by typing a message below.
inputPlaceholder={{INPUT_PLACEHOLDER}}

# Buttons
btnNewThread=New Thread
btnLoadAgentCard=Refresh Agent

# Messages
msgWorking=Your agent is thinking...
msgRefreshingAgent=Refreshing agent connection...
msgNewThread=New conversation started.
msgError=Something went wrong. Make sure the agent is running on localhost:{{PORT}}.

# Disclaimer
chatDisclaimer=AI-generated responses. Always verify important information independently.
```

> Customize `inputPlaceholder` and `chatDisclaimer` to fit the agent's domain. The `msgError` port is already substituted.

---

## Step 4 — Confirm

Print a summary of what was created:

```
Created:
  {{AGENT_NAME}}/app/package.json
  {{AGENT_NAME}}/app/ui5.yaml
  {{AGENT_NAME}}/app/webapp/index.html
  {{AGENT_NAME}}/app/webapp/Component.js
  {{AGENT_NAME}}/app/webapp/manifest.json
  {{AGENT_NAME}}/app/webapp/model/models.js
  {{AGENT_NAME}}/app/webapp/service/A2AService.js
  {{AGENT_NAME}}/app/webapp/controller/App.controller.js
  {{AGENT_NAME}}/app/webapp/controller/Chat.controller.js
  {{AGENT_NAME}}/app/webapp/view/App.view.xml
  {{AGENT_NAME}}/app/webapp/view/Chat.view.xml
  {{AGENT_NAME}}/app/webapp/css/style.css
  {{AGENT_NAME}}/app/webapp/i18n/i18n.properties
```

Then tell the user how to start the UI:

```
To start the Fiori UI:
  cd {{AGENT_NAME}}/app
  npm install
  npm start        # opens http://localhost:{{FIORI_PORT}}/index.html

Make sure the agent is already running on port {{PORT}}:
  cd {{AGENT_NAME}} && python main.py
```

---

## Reference: How the proxy works

`ui5-middleware-simpleproxy` intercepts all requests to `/api/agent/*` from the browser and forwards them to `http://localhost:{{PORT}}/*`. This avoids CORS issues. The `A2AService.js` always calls `AGENT_BASE = "/api/agent"`, so the same service file works in development (proxied) and in any deployment where the UI is served from the same origin as the agent.

## Reference: Theming

The app uses `sap_horizon` theme. To switch themes, change `data-sap-ui-theme` in `index.html`. Available built-in themes: `sap_horizon`, `sap_horizon_dark`, `sap_fiori_3`, `sap_fiori_3_dark`.
