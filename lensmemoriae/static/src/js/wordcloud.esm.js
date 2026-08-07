/** @odoo-module **/

import {Component, useRef, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";

function wordColor(word) {
    let hash = 0;
    for (let i = 0; i < word.length; i++) {
        hash = word.charCodeAt(i) + ((hash << 5) - hash);
    }
    return `hsl(${Math.abs(hash) % 360}, 55%, 40%)`;
}

class LensMemoriaeWordCloud extends Component {
    static template = "lensmemoriae.WordCloud";

    setup() {
        this.state = useState({
            loading: true,
            wordCount: 0,
            wordLimit: 80,
            totalWords: 0,
            hovered: null,
            tooltipX: 0,
            tooltipY: 0,
        });
        this.canvasRef = useRef("canvas");
        this.orm = useService("orm");
        this.action = useService("action");
        this.wordRects = [];
        this.wordData = [];
        this.loadData();
    }

    async loadData() {
        try {
            const wordData = await this.orm.call(
                "lensmemoriae.image",
                "get_word_cloud_data",
                []
            );
            this.allWordData = wordData || [];
            this.state.totalWords = this.allWordData.length;
            this.state.wordLimit = Math.min(80, this.state.totalWords) || 1;
            this.state.wordCount = this.state.wordLimit;
        } catch (_e) {
            // Silent
        }
        this.state.loading = false;
        await new Promise((r) => setTimeout(r, 200));
        this.renderCloud();
    }

    onLimitChange(ev) {
        const value = parseInt(ev.target.value, 10);
        if (Number.isNaN(value)) return;
        this.state.wordLimit = Math.max(1, Math.min(value, this.state.totalWords));
        if (this._renderTimer) clearTimeout(this._renderTimer);
        this._renderTimer = setTimeout(() => {
            this.renderCloud();
            this._renderTimer = null;
        }, 50);
    }

    renderCloud() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const W = Math.floor(window.innerWidth - 60);
        const H = Math.floor(window.innerHeight - 150);

        if (W <= 10 || H <= 10) {
            setTimeout(() => this.renderCloud(), 200);
            return;
        }

        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + "px";
        canvas.style.height = H + "px";
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, W, H);

        this.wordData = this.allWordData.slice(0, this.state.wordLimit);
        this.state.wordCount = this.wordData.length;

        if (!this.wordData.length) {
            ctx.fillStyle = "#6c757d";
            ctx.font = '18px "Helvetica Neue", Arial, sans-serif';
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("No words found in descriptions", W / 2, H / 2);
            return;
        }

        const maxCount = this.allWordData[0].count;
        this.wordRects = [];
        const placed = [];
        const cx = W / 2;
        const cy = H / 2;

        for (const item of this.wordData) {
            const ratio = item.count / maxCount;
            const fontSize = 14 + 50 * Math.sqrt(ratio);
            const font = `600 ${fontSize}px "Helvetica Neue", Arial, sans-serif`;
            ctx.font = font;
            const tw = ctx.measureText(item.word).width;
            const th = fontSize * 1.25;
            const padX = 6;
            const padY = 4;
            const rw = tw + padX * 2;
            const rh = th + padY * 2;

            let px = cx - rw / 2;
            let py = cy - rh / 2;
            let placedOk = false;
            let angle = 0;
            let radius = 0;

            for (let iter = 0; iter < 4000; iter++) {
                const r = {x: px, y: py, w: rw, h: rh};
                if (
                    px >= 0 &&
                    py >= 0 &&
                    px + rw <= W &&
                    py + rh <= H &&
                    !placed.some((p) => this.overlap(r, p))
                ) {
                    placed.push(r);
                    this.wordRects.push({...r, word: item.word, count: item.count});
                    ctx.font = font;
                    ctx.textAlign = "left";
                    ctx.textBaseline = "top";
                    ctx.fillStyle = wordColor(item.word);
                    ctx.fillText(item.word, px + padX, py + padY);
                    placedOk = true;
                    break;
                }
                angle += 0.3;
                radius += 1.2;
                px = cx + Math.cos(angle) * radius - rw / 2;
                py = cy + Math.sin(angle) * radius - rh / 2;
            }

            if (!placedOk) {
                for (let i = 0; i < 200; i++) {
                    px = Math.random() * (W - rw);
                    py = Math.random() * (H - rh);
                    const r = {x: px, y: py, w: rw, h: rh};
                    if (!placed.some((p) => this.overlap(r, p))) {
                        placed.push(r);
                        this.wordRects.push({...r, word: item.word, count: item.count});
                        ctx.font = font;
                        ctx.textAlign = "left";
                        ctx.textBaseline = "top";
                        ctx.fillStyle = wordColor(item.word);
                        ctx.fillText(item.word, px + padX, py + padY);
                        break;
                    }
                }
            }
        }
    }

    overlap(a, b) {
        return !(
            a.x + a.w < b.x ||
            b.x + b.w < a.x ||
            a.y + a.h < b.y ||
            b.y + b.h < a.y
        );
    }

    onHover(ev) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;
        const cr = canvas.getBoundingClientRect();
        const mx = ev.clientX - cr.left;
        const my = ev.clientY - cr.top;

        for (let i = this.wordRects.length - 1; i >= 0; i--) {
            const wr = this.wordRects[i];
            if (mx >= wr.x && mx <= wr.x + wr.w && my >= wr.y && my <= wr.y + wr.h) {
                if (!this.state.hovered || this.state.hovered.word !== wr.word) {
                    this.state.hovered = {word: wr.word, count: wr.count};
                    this.state.tooltipX = ev.clientX;
                    this.state.tooltipY = ev.clientY;
                }
                canvas.style.cursor = "pointer";
                return;
            }
        }
        if (this.state.hovered) this.state.hovered = null;
        canvas.style.cursor = "default";
    }

    onLeave() {
        this.state.hovered = null;
    }

    onClick(ev) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;
        const cr = canvas.getBoundingClientRect();
        const mx = ev.clientX - cr.left;
        const my = ev.clientY - cr.top;

        for (let i = this.wordRects.length - 1; i >= 0; i--) {
            const wr = this.wordRects[i];
            if (mx >= wr.x && mx <= wr.x + wr.w && my >= wr.y && my <= wr.y + wr.h) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    name: `"${wr.word}"`,
                    res_model: "lensmemoriae.image",
                    views: [
                        [false, "kanban"],
                        [false, "list"],
                        [false, "form"],
                    ],
                    domain: [
                        ["description_approved", "=", true],
                        ["description", "ilike", wr.word],
                    ],
                    context: {},
                    target: "current",
                });
                return;
            }
        }
    }
}

registry.category("actions").add("lensmemoriae.word_cloud", LensMemoriaeWordCloud);
