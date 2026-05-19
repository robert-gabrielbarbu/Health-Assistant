/**
 * A2AService — JSON-RPC 2.0 client for the A2A agent running at localhost:8080.
 * Requests are routed through the ui5-middleware-simpleproxy at /api/agent
 * to avoid CORS restrictions in the browser.
 *
 * A2A protocol reference: https://google.github.io/A2A
 * Endpoint:  POST /api/agent/         (proxied → http://localhost:8080/)
 * Agent card: GET /api/agent/.well-known/agent.json
 */
sap.ui.define([], function () {
    "use strict";

    const AGENT_BASE = "/api/agent";

    // ── Helpers ────────────────────────────────────────────────────────────

    function _rpcId() {
        return "rpc-" + Date.now() + "-" + Math.floor(Math.random() * 10000);
    }

    function _msgId() {
        return "msg-" + Date.now() + "-" + Math.floor(Math.random() * 10000);
    }

    /**
     * Extract the final text content from an A2A Task result.
     * Checks artifacts first, then status.message.
     */
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
        // fall back to status message
        const msg = task.status && task.status.message;
        if (msg && msg.parts) {
            for (const part of msg.parts) {
                if (part.kind === "text" && part.text) return part.text;
            }
        }
        return "";
    }

    // ── Public API ─────────────────────────────────────────────────────────

    const A2AService = {

        /**
         * Fetch the agent card (name, description, skills, etc.)
         * @returns {Promise<object>} AgentCard object
         */
        getAgentCard: async function () {
            const resp = await fetch(AGENT_BASE + "/.well-known/agent.json");
            if (!resp.ok) throw new Error("Agent card request failed: " + resp.status);
            return resp.json();
        },

        /**
         * Send a user message to the agent and wait for a complete response.
         *
         * @param {string} text       The user's message text
         * @param {string} [contextId] Existing thread context ID (undefined = new thread)
         * @param {function} [onStatus] Optional callback(statusMessage) for interim updates
         * @returns {Promise<{text: string, contextId: string, taskId: string}>}
         */
        sendMessage: async function (text, contextId, onStatus) {
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

        /**
         * Stream a user message using SSE (message/stream).
         * Falls back to sendMessage if streaming is not supported.
         *
         * @param {string}   text
         * @param {string}   [contextId]
         * @param {function} onChunk(text, isDone, contextId)  called per chunk
         * @returns {Promise<{contextId: string}>}
         */
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
                // streaming not available — fall back
                const result = await this.sendMessage(text, contextId);
                onChunk(result.text, true, result.contextId);
                return { contextId: result.contextId };
            }

            const contentType = resp.headers.get("content-type") || "";
            if (!resp.ok || !resp.body || !contentType.includes("text/event-stream")) {
                // server doesn't support message/stream — fall back to blocking send
                const result = await this.sendMessage(text, contextId);
                onChunk(result.text, true, result.contextId);
                return { contextId: result.contextId };
            }

            // parse SSE stream
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
                buffer = lines.pop(); // keep incomplete last line

                for (const line of lines) {
                    if (!line.startsWith("data:")) continue;
                    const raw = line.slice(5).trim();
                    if (!raw || raw === "[DONE]") continue;
                    try {
                        const event = JSON.parse(raw);
                        const result = event.result;
                        if (!result) continue;

                        if (result.contextId) finalContextId = result.contextId;

                        // working status
                        if (result.status && result.status.state === "working") {
                            const statusText = _extractText({ status: result.status });
                            if (statusText) onChunk(statusText, false, finalContextId);
                        }

                        // artifact chunk — track text; only mark done on lastChunk
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

                        // completed status — skip if artifact already fired done;
                        // use accumulated artifact text as fallback when event has none
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

            // stream ended without a done signal — fall back to blocking send
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
