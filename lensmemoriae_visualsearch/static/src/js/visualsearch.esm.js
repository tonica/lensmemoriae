/** @odoo-module **/

import {Component, useEffect, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class LensMemoriaeVisualSearch extends Component {
    static template = "lensmemoriae.VisualSearch";

    setup() {
        this.state = useState({
            queryImage: null,
            results: [],
            fitted: {},
            searching: false,
            searched: false,
            error: null,
            dragOver: false,
            threshold: 14,
            limit: 20,
        });
        this.fileInputRef = useRef("fileInput");
        this.http = useService("http");
        this.action = useService("action");

        useEffect(
            () => {
                const handler = (ev) => this.onPaste(ev);
                window.addEventListener("paste", handler);
                return () => window.removeEventListener("paste", handler);
            },
            () => []
        );
    }

    onPaste(ev) {
        if (!ev.clipboardData) return;
        const items = ev.clipboardData.items || [];
        for (const item of items) {
            if (item.kind === "file" && item.type.startsWith("image/")) {
                const file = item.getAsFile();
                if (file) {
                    ev.preventDefault();
                    this.readFile(file);
                    return;
                }
            }
        }
    }

    onDrop(ev) {
        this.state.dragOver = false;
        const file = ev.dataTransfer && ev.dataTransfer.files
            ? ev.dataTransfer.files[0]
            : null;
        if (file && file.type.startsWith("image/")) {
            this.readFile(file);
        }
    }

    onFileInput(ev) {
        const file = ev.target.files[0];
        if (file) {
            this.readFile(file);
        }
        ev.target.value = "";
    }

    readFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.state.queryImage = e.target.result;
            this.state.searched = false;
            this.state.results = [];
            this.state.error = null;
        };
        reader.readAsDataURL(file);
    }

    async onSearch() {
        if (!this.state.queryImage) return;
        this.state.searching = true;
        this.state.error = null;
        this.state.fitted = {};
        try {
            const res = await this.http.post("/lens-memoriae/visual-search", {
                image: this.state.queryImage,
                limit: this.state.limit,
                threshold: this.state.threshold,
            });
            if (res && res.error) {
                this.state.results = [];
                this.state.error = res.error;
            } else {
                this.state.results = (res && res.results) || [];
            }
            this.state.searched = true;
        } catch (e) {
            this.state.results = [];
            this.state.error = "Search failed.";
        } finally {
            this.state.searching = false;
        }
    }

    clearQuery() {
        this.state.queryImage = null;
        this.state.results = [];
        this.state.fitted = {};
        this.state.error = null;
        this.state.searched = false;
    }

    onThumbLoad(result, ev) {
        const img = ev.target;
        if (!img || !img.naturalWidth || !img.naturalHeight) return;
        const cw = img.clientWidth || img.width;
        const ch = img.clientHeight || img.height;
        const scale = Math.min(cw / img.naturalWidth, ch / img.naturalHeight);
        const w = img.naturalWidth * scale;
        const h = img.naturalHeight * scale;
        const x = (cw - w) / 2;
        const y = (ch - h) / 2;
        this.state.fitted[result.id] = {x, y, w, h};
    }

    regionStyle(result) {
        const rect = this.state.fitted[result.id];
        const r = result.best_region;
        if (!rect || !r) return "";
        const x = rect.x + r.x * rect.w;
        const y = rect.y + r.y * rect.h;
        const width = r.width * rect.w;
        const height = r.height * rect.h;
        return `left:${x}px; top:${y}px; width:${width}px; height:${height}px;`;
    }

    simClass(sim) {
        if (sim >= 80) return "vs-badge vs-badge-success";
        if (sim >= 55) return "vs-badge vs-badge-warning";
        return "vs-badge vs-badge-danger";
    }

    openResult(result) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "lensmemoriae.image",
            res_id: result.id,
            view_mode: "form",
            target: "current",
        });
    }
}

registry.category("actions").add(
    "lensmemoriae.visual_search",
    LensMemoriaeVisualSearch
);