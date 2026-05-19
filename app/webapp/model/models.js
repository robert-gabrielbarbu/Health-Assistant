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
