sap.ui.define([
    "sap/ui/core/mvc/Controller"
], function (Controller) {
    "use strict";

    return Controller.extend("com.coach.agent.controller.App", {
        onInit: function () {
            // Apply compact density on desktop
            if (sap.ui.Device.system.desktop) {
                this.getView().addStyleClass("sapUiSizeCompact");
            }
        }
    });
});
