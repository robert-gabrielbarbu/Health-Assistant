sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "com/coach/agent/service/A2AService"
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

    return Controller.extend("com.coach.agent.controller.Chat", {

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
