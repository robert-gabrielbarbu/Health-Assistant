sap.ui.define([
    "sap/ui/core/UIComponent",
    "sap/ui/Device",
    "com/coach/agent/model/models"
], function (UIComponent, Device, models) {
    "use strict";

    return UIComponent.extend("com.coach.agent.Component", {

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
