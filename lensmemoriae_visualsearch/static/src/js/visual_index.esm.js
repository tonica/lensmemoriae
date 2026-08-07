/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class LensMemoriaeVisualIndex extends Component {
    static template = "lensmemoriae.VisualIndex";

    setup() {
        this.state = useState({
            stats: {total: 0, indexed: 0, pending: 0, error: 0, progress: 0},
            images: [],
            filter: "pending",
            busy: false,
        });
        this.orm = useService("orm");
        this.action = useService("action");
        this.notify = useService("notification");
        this.loadStats();
        this.loadImages();
    }

    async loadStats() {
        try {
            this.state.stats = await this.orm.call(
                "lensmemoriae.image",
                "visual_index_stats"
            );
        } catch (e) {
            this.state.stats = {total: 0, indexed: 0, pending: 0, error: 0, progress: 0};
        }
    }

    async loadImages() {
        try {
            this.state.images = await this.orm.searchRead(
                "lensmemoriae.image",
                [
                    ["image", "!=", false],
                    ["visual_index_state", "=", this.state.filter],
                ],
                ["id", "name"],
                {limit: 100, order: "visual_index_date desc"}
            );
        } catch (e) {
            this.state.images = [];
        }
    }

    onChangeFilter(ev) {
        this.state.filter = ev.target.value;
        this.loadImages();
    }

    async runIndex(method, args, message) {
        if (this.state.busy) return;
        this.state.busy = true;
        try {
            const count = await this.orm.call("lensmemoriae.image", method, args);
            this.notify.add(message.replace("%s", String(count)), {
                title: "Visual Index",
                type: "success",
            });
            await this.loadStats();
            await this.loadImages();
        } catch (e) {
            this.notify.add("The operation failed.", {
                title: "Visual Index",
                type: "danger",
            });
        } finally {
            this.state.busy = false;
        }
    }

    onIndexPending() {
        this.runIndex("_cron_visual_index", [100000], "%s image(s) indexed.");
    }

    onReindexAll() {
        this.runIndex("_reindex_all", [], "%s image(s) reindexed.");
    }

    openImage(img) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "lensmemoriae.image",
            res_id: img.id,
            view_mode: "form",
            target: "current",
        });
    }
}

registry.category("actions").add(
    "lensmemoriae.visual_index",
    LensMemoriaeVisualIndex
);