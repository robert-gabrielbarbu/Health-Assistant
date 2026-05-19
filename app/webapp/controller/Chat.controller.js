sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "sap/m/Dialog",
    "sap/m/Button",
    "sap/m/VBox",
    "sap/m/HBox",
    "sap/m/Text",
    "sap/m/BusyIndicator",
    "sap/ui/core/Icon",
    "com/coach/agent/service/A2AService"
], function (Controller, MessageToast, MessageBox, Dialog, Button, VBox, HBox, Text, BusyIndicator, Icon, A2AService) {
    "use strict";

    // ── Markdown → HTML ────────────────────────────────────────────────────
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

    // ── Medical specialty detection ─────────────────────────────────────────
    var SPECIALTY_MAP = [
        { keywords: ["cardio", "heart", "cardiac", "chest pain", "arrhythmia", "ecg", "blood pressure"], specialty: "cardiologist" },
        { keywords: ["neuro", "brain", "headache", "migraine", "stroke", "seizure", "epilepsy", "nerve"], specialty: "neurologist" },
        { keywords: ["ortho", "bone", "joint", "spine", "fracture", "knee", "hip", "shoulder", "arthritis"], specialty: "orthopedic" },
        { keywords: ["dermat", "skin", "rash", "acne", "eczema", "psoriasis", "mole"], specialty: "dermatologist" },
        { keywords: ["gastro", "stomach", "bowel", "colon", "liver", "intestin", "digest", "ibs", "crohn"], specialty: "gastroenterologist" },
        { keywords: ["pulmon", "lung", "asthma", "copd", "breath", "respiratory", "bronch"], specialty: "pulmonologist" },
        { keywords: ["oncol", "cancer", "tumor", "chemo", "radiation", "malignant"], specialty: "oncologist" },
        { keywords: ["endocrin", "diabetes", "thyroid", "hormone", "insulin", "metabolic"], specialty: "endocrinologist" },
        { keywords: ["ophthalm", "eye", "vision", "retina", "glaucoma", "cataract"], specialty: "ophthalmologist" },
        { keywords: ["psych", "anxiety", "depression", "mental", "bipolar", "schizo", "therapy"], specialty: "psychiatrist" },
        { keywords: ["uro", "kidney", "bladder", "prostate", "urinary", "renal"], specialty: "urologist" },
        { keywords: ["gynecol", "obstet", "uterus", "ovarian", "cervical", "pregnancy", "menstrual"], specialty: "gynecologist" },
        { keywords: ["pediatr", "child", "infant", "toddler", "newborn"], specialty: "pediatrician" },
        { keywords: ["allerg", "asthma", "immunol", "autoimmune", "hive", "anaphyl"], specialty: "allergist" },
        { keywords: ["rheumat", "lupus", "fibromyalgia", "autoimmune", "inflammation"], specialty: "rheumatologist" }
    ];

    function _detectSpecialty(text) {
        if (!text) return "doctor";
        var lower = text.toLowerCase();
        for (var i = 0; i < SPECIALTY_MAP.length; i++) {
            var entry = SPECIALTY_MAP[i];
            for (var j = 0; j < entry.keywords.length; j++) {
                if (lower.indexOf(entry.keywords[j]) !== -1) {
                    return entry.specialty;
                }
            }
        }
        return "doctor";
    }

    function _hasMedicalContent(text) {
        if (!text) return false;
        var lower = text.toLowerCase();
        var medicalTerms = [
            "cardio", "heart", "neuro", "brain", "ortho", "bone", "dermat", "skin",
            "gastro", "stomach", "pulmon", "lung", "cancer", "tumor", "oncol",
            "diabetes", "thyroid", "eye", "vision", "psych", "anxiety", "depression",
            "kidney", "bladder", "gynecol", "pediatr", "allerg", "rheumat",
            "symptom", "diagnos", "treatment", "medication", "doctor", "specialist",
            "blood pressure", "cholesterol", "surgery", "hospital", "clinic",
            "what this document says", "what you should do", "recommendations"
        ];
        for (var i = 0; i < medicalTerms.length; i++) {
            if (lower.indexOf(medicalTerms[i]) !== -1) return true;
        }
        return false;
    }

    // ── Controller ─────────────────────────────────────────────────────────
    return Controller.extend("com.coach.agent.controller.Chat", {

        onInit: function () {
            this._loadAgentCard();
            this._doctorsDialog = null;
        },

        _loadAgentCard: function () {
            var oModel = this._chatModel();
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
            var oModel = this._chatModel();
            oModel.setProperty("/contextId", null);
            oModel.setProperty("/messages", []);
            oModel.setProperty("/statusMessage", "");
            MessageToast.show(this._i18n("msgNewThread"));
        },

        onSend: function () {
            var oInput = this.byId("userInput");
            var sText = (oInput.getValue() || "").trim();
            if (!sText) return;

            oInput.setValue("");

            var oModel = this._chatModel();
            var sContextId = oModel.getProperty("/contextId");

            this._appendMessage("user", sText);
            oModel.setProperty("/isLoading", true);
            oModel.setProperty("/statusMessage", this._i18n("msgWorking"));

            var that = this;

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

        onUploadPdf: function () {
            var that = this;
            var oInput = document.getElementById("pdfUploadInput");
            if (!oInput) return;

            oInput.onchange = function (e) {
                var file = e.target.files[0];
                if (!file) return;
                oInput.value = "";

                var oModel = that._chatModel();
                oModel.setProperty("/isLoading", true);
                oModel.setProperty("/statusMessage", "Reading PDF...");

                var formData = new FormData();
                formData.append("file", file);

                fetch("/api/agent/parse-pdf", { method: "POST", body: formData })
                    .then(function (resp) { return resp.json(); })
                    .then(function (data) {
                        oModel.setProperty("/isLoading", false);
                        oModel.setProperty("/statusMessage", "");
                        if (data.error) {
                            MessageBox.error("PDF error: " + data.error);
                            return;
                        }
                        if (!data.text || data.text.trim().length < 20) {
                            MessageBox.error("Could not read text from this PDF. Make sure it is not a scanned image.");
                            return;
                        }
                        var prompt = "You are a helpful medical translator. Analyze the following medical document and respond in this exact structure:\n\n**What this document says** (2-3 sentences in plain language, no jargon)\n\n**What you should do next** (bullet points with clear action steps)\n\n**Recommendations** (bullet points with practical advice)\n\nKeep the entire response short and simple, as if explaining to someone with no medical background.\n\nDocument:\n\n" + data.text.substring(0, 8000);
                        that.byId("userInput").setValue(prompt);
                        MessageToast.show("PDF loaded — press Send to translate.");
                    })
                    .catch(function () {
                        oModel.setProperty("/isLoading", false);
                        oModel.setProperty("/statusMessage", "");
                        MessageBox.error("Failed to upload the PDF. Make sure the agent is running.");
                    });
            };
            oInput.click();
        },

        // ── Google Maps: Find nearby doctors ───────────────────────────────
        onFindDoctors: function (oEvent) {
            var oButton = oEvent.getSource();
            var oContext = oButton.getBindingContext("chat");
            var specialty = "doctor";
            if (oContext) {
                var msgContent = oContext.getProperty("content") || "";
                specialty = _detectSpecialty(msgContent);
            } else {
                // fall back to last agent message
                var msgs = this._chatModel().getProperty("/messages") || [];
                for (var i = msgs.length - 1; i >= 0; i--) {
                    if (msgs[i].role === "agent") {
                        specialty = _detectSpecialty(msgs[i].content);
                        break;
                    }
                }
            }
            this._openDoctorsDialog(specialty);
        },

        _openDoctorsDialog: function (specialty) {
            var that = this;

            // Create dialog lazily
            if (!this._doctorsDialog) {
                this._doctorsDialog = new Dialog({
                    title: "Nearby Specialists",
                    contentWidth: "480px",
                    contentHeight: "420px",
                    resizable: true,
                    endButton: new Button({
                        text: "Close",
                        press: function () { that._doctorsDialog.close(); }
                    })
                });
                this.getView().addDependent(this._doctorsDialog);
            }

            // Show busy state
            var oBusy = new BusyIndicator({ size: "1rem" });
            var oContent = new VBox({
                items: [
                    new Text({ text: "Locating you and searching for " + specialty + "s nearby…", wrapping: true })
                        .addStyleClass("sapUiSmallMarginBottom"),
                    oBusy
                ]
            }).addStyleClass("sapUiSmallMargin");
            this._doctorsDialog.removeAllContent();
            this._doctorsDialog.addContent(oContent);
            this._doctorsDialog.setTitle("Finding " + specialty + "s near you…");
            this._doctorsDialog.open();

            // Get geolocation then call backend proxy
            if (!navigator.geolocation) {
                that._showDoctorsError("Geolocation is not supported by your browser.");
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function (pos) {
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    fetch("/api/agent/nearby-doctors?lat=" + lat + "&lng=" + lng + "&specialty=" + encodeURIComponent(specialty))
                        .then(function (r) { return r.json(); })
                        .then(function (data) { that._renderDoctorsResults(data, specialty, lat, lng); })
                        .catch(function () { that._showDoctorsError("Could not reach the server. Make sure the agent is running."); });
                },
                function () {
                    that._showDoctorsError("Location access denied. Please allow location in your browser.");
                }
            );
        },

        _renderDoctorsResults: function (data, specialty, lat, lng) {
            var that = this;
            var places = (data && data.places) || [];

            this._doctorsDialog.setTitle("🗺 " + specialty.charAt(0).toUpperCase() + specialty.slice(1) + "s nearby");
            this._doctorsDialog.removeAllContent();

            if (!places.length) {
                this._doctorsDialog.addContent(
                    new VBox({ items: [new Text({ text: "No results found nearby. Try a broader search.", wrapping: true })] })
                        .addStyleClass("sapUiSmallMargin")
                );
                return;
            }

            var oList = new VBox({ width: "100%" });
            places.forEach(function (p) {
                var stars = p.rating ? "★ " + p.rating : "";
                var reviews = p.user_ratings_total ? " (" + p.user_ratings_total + ")" : "";
                var openText = p.open_now === true ? " · Open now" : p.open_now === false ? " · Closed" : "";
                var mapsUrl = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent((p.name || "") + " " + (p.address || "")) + (p.place_id ? "&query_place_id=" + p.place_id : "");

                var oCard = new VBox({
                    items: [
                        new HBox({
                            alignItems: "Center",
                            items: [
                                new Icon({ src: "sap-icon://hospital", color: "#4db8ff", size: "1rem" }).addStyleClass("sapUiTinyMarginEnd"),
                                new Text({ text: p.name || "Unknown", wrapping: true }).addStyleClass("doctorName")
                            ]
                        }),
                        new Text({ text: (p.address || "Address not available"), wrapping: true }).addStyleClass("doctorAddress"),
                        new HBox({
                            items: [
                                new Text({ text: stars + reviews + openText }).addStyleClass("doctorMeta"),
                                new Button({
                                    text: "Open in Maps",
                                    type: "Transparent",
                                    press: function () { window.open(mapsUrl, "_blank"); }
                                }).addStyleClass("doctorMapsBtn")
                            ],
                            justifyContent: "SpaceBetween",
                            width: "100%"
                        })
                    ]
                }).addStyleClass("doctorCard");
                oList.addItem(oCard);
            });

            var oScroll = new sap.m.ScrollContainer({
                content: [oList],
                vertical: true,
                height: "360px",
                width: "100%"
            });
            this._doctorsDialog.addContent(oScroll);
        },

        _showDoctorsError: function (msg) {
            this._doctorsDialog.removeAllContent();
            this._doctorsDialog.setTitle("Could not load doctors");
            this._doctorsDialog.addContent(
                new VBox({ items: [new Text({ text: msg, wrapping: true })] }).addStyleClass("sapUiSmallMargin")
            );
        },

        // ── Helpers ────────────────────────────────────────────────────────
        _appendMessage: function (sRole, sText) {
            var oModel = this._chatModel();
            var aMessages = oModel.getProperty("/messages") || [];
            aMessages.push({
                role: sRole,
                content: sText,
                contentHtml: _mdToHtml(sText),
                hasMedicalContent: sRole === "agent" && _hasMedicalContent(sText),
                detectedSpecialty: sRole === "agent" ? _detectSpecialty(sText) : ""
            });
            oModel.setProperty("/messages", aMessages);
        },

        _scrollToBottom: function () {
            var oDomRef = this.byId("chatArea").getDomRef();
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
