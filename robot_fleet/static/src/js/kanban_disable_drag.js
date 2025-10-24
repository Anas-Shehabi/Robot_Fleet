//import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
//import { patch } from "@web/core/utils/patch";
//import { useService } from "@web/core/utils/hooks";
//
//const patchKanban = (KanbanRenderer) => {
//    patch(KanbanRenderer.prototype, {
//        setup() {
//            super.setup(...arguments);
//            this.user = useService("user");
//
//            // Only apply if this is our specific Kanban
//            if (this.env.qweb.kanbanViewEl?.classList.contains('robot_fleet_kanban')) {
//                if (this.user.hasGroup('robot_fleet.group_client')) {
//                    this.props.draggable = false;
//                    this.props.sortable = false;
//                    console.log("✅ Disabled drag for robot_fleet kanban");
//                }
//            }
//        }
//    });
//    return KanbanRenderer;
//};
//
//// Register our patched renderer
//odoo.define('robot_fleet.kanban_patch', function (require) {
//    "use strict";
//
//    const { kanbanView } = require('web.KanbanView');
//    const KanbanRenderer = require('web.KanbanRenderer');
//
//    patchKanban(KanbanRenderer);
//});