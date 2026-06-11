/** @odoo-module **/

import {registry} from "@web/core/registry";

const STORAGE_KEY = "lensmemoriae_kanban_size";
const CINEMA_ACTIVE_CLASS = "lensmemoriae-cinema-active";

function qs(sel) {
    return document.querySelector(sel);
}

function qsa(sel) {
    return Array.from(document.querySelectorAll(sel));
}

function escaped(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function getSavedSize() {
    try {
        var v = localStorage.getItem(STORAGE_KEY);
        if (v === "small") return 160;
        if (v === "medium") return 220;
        if (v === "large") return 320;
        var n = parseInt(v, 10);
        if (!isNaN(n) && n >= 100 && n <= 500) return n;
    } catch (_e) {
        /**/
    }
    return 220;
}

function saveSize(value) {
    try {
        localStorage.setItem(STORAGE_KEY, String(value));
    } catch (_e) {
        /**/
    }
}

function getSelectedIds() {
    return qsa(".lensmemoriae-kanban .o_kanban_record input[type='checkbox']:checked")
        .map(function (cb) {
            var rec = cb.closest(".o_kanban_record");
            return parseInt(rec ? rec.dataset.id : "0", 10);
        })
        .filter(function (id) {
            return id > 0;
        });
}

function getCardIndex(imgEl) {
    var all = qsa(".lensmemoriae-kanban .lensmemoriae-grid-img");
    return all.indexOf(imgEl);
}

function getCardCount() {
    return qsa(".lensmemoriae-kanban .lensmemoriae-grid-img").length;
}

var cinema = {
    overlay: null,
    currentIndex: -1,
    images: [],
};

function getFullResSrc(src) {
    return src.replace(/\/\d+x\d+$/, "");
}

function getMetaForIndex(idx) {
    var all = qsa(".lensmemoriae-kanban .lensmemoriae-grid-img");
    var img = all[idx];
    if (!img) return null;
    var record = img.closest(".o_kanban_record");
    if (!record) return null;
    var nameEl = record.querySelector(".lensmemoriae-overlay-name");
    var tagsEl = record.querySelector(".lensmemoriae-overlay-tags");
    var name = nameEl ? nameEl.textContent.trim() : "";
    var tags = tagsEl ? tagsEl.textContent.trim() : "";
    return {name: name, tags: tags, src: img.getAttribute("src")};
}

function renderCinemaInfo(idx) {
    var meta = getMetaForIndex(idx);
    if (!meta) return "";
    var tagsHtml = meta.tags
        ? '<span class="lensmemoriae-cinema-tags">' + meta.tags + "</span>"
        : "";
    return (
        '<div class="lensmemoriae-cinema-info">' +
        '<span class="lensmemoriae-cinema-name">' +
        escaped(meta.name) +
        "</span>" +
        tagsHtml +
        '<span class="lensmemoriae-cinema-counter">' +
        (idx + 1) +
        " / " +
        getCardCount() +
        "</span>" +
        "</div>"
    );
}

function showCinemaImage(idx) {
    var all = qsa(".lensmemoriae-kanban .lensmemoriae-grid-img");
    var img = all[idx];
    if (!img) return;
    cinema.currentIndex = idx;
    var fullSrc = getFullResSrc(img.getAttribute("src"));
    var cinemaImg = cinema.overlay.querySelector(".lensmemoriae-cinema-img");
    cinemaImg.setAttribute("src", fullSrc);
    cinema.overlay.querySelector(".lensmemoriae-cinema-info-wrap").innerHTML =
        renderCinemaInfo(idx);
    cinema.overlay
        .querySelector(".lensmemoriae-cinema-prev")
        .classList.toggle("o_hidden", idx <= 0);
    cinema.overlay
        .querySelector(".lensmemoriae-cinema-next")
        .classList.toggle("o_hidden", idx >= all.length - 1);
}

/* eslint-disable no-use-before-define */
function closeCinema() {
    if (!cinema.overlay) return;
    cinema.overlay.remove();
    cinema.overlay = null;
    cinema.currentIndex = -1;
    document.removeEventListener("keydown", cinemaKeyHandler);
    document.body.classList.remove(CINEMA_ACTIVE_CLASS);
}

function cinemaKeyHandler(ev) {
    if (!cinema.overlay) return;
    if (ev.key === "Escape") {
        closeCinema();
    } else if (ev.key === "ArrowLeft") {
        showCinemaImage(cinema.currentIndex - 1);
    } else if (ev.key === "ArrowRight") {
        showCinemaImage(cinema.currentIndex + 1);
    }
}

function openCinema(imgEl) {
    if (cinema.overlay) return;
    var idx = getCardIndex(imgEl);
    if (idx < 0) return;

    cinema.overlay = document.createElement("div");
    cinema.overlay.className = "lensmemoriae-cinema";
    cinema.overlay.innerHTML =
        '<div class="lensmemoriae-cinema-bg"></div>' +
        '<button class="lensmemoriae-cinema-close" title="Close (Esc)">&times;</button>' +
        '<button class="lensmemoriae-cinema-prev" title="Previous (&larr;)">&#8249;</button>' +
        '<button class="lensmemoriae-cinema-next" title="Next (&rarr;)">&#8250;</button>' +
        '<div class="lensmemoriae-cinema-viewport">' +
        '<img class="lensmemoriae-cinema-img" alt="" />' +
        "</div>" +
        '<div class="lensmemoriae-cinema-info-wrap"></div>';
    document.body.appendChild(cinema.overlay);

    showCinemaImage(idx);

    cinema.overlay
        .querySelector(".lensmemoriae-cinema-close")
        .addEventListener("click", closeCinema);
    cinema.overlay
        .querySelector(".lensmemoriae-cinema-bg")
        .addEventListener("click", closeCinema);
    cinema.overlay
        .querySelector(".lensmemoriae-cinema-prev")
        .addEventListener("click", function () {
            showCinemaImage(cinema.currentIndex - 1);
        });
    cinema.overlay
        .querySelector(".lensmemoriae-cinema-next")
        .addEventListener("click", function () {
            showCinemaImage(cinema.currentIndex + 1);
        });
    document.addEventListener("keydown", cinemaKeyHandler);
    document.body.classList.add(CINEMA_ACTIVE_CLASS);
}

function attachCinemaListeners() {
    document.addEventListener("click", function (ev) {
        var target = ev.target.closest(".lensmemoriae-grid-img");
        if (!target) return;
        if (target.closest(".o_kanban_record input[type='checkbox']")) return;
        ev.preventDefault();
        openCinema(target);
    });
}

function getKanbanRenderer() {
    var kanban = qs(".lensmemoriae-kanban");
    if (!kanban) return null;
    return kanban.closest(".o_kanban_renderer");
}

function applyCardWidth(value) {
    var renderer = getKanbanRenderer();
    if (!renderer) return;
    renderer.style.setProperty("--lens-card-width", value + "px");
}

function attachSizeListeners() {
    document.addEventListener("input", function (ev) {
        if (!ev.target.classList.contains("lensmemoriae-size-slider")) {
            return;
        }
        var value = parseInt(ev.target.value, 10);
        var bar = ev.target.closest(".lensmemoriae-size-bar");
        if (bar) {
            var display = bar.querySelector(".lensmemoriae-size-value");
            if (display) display.textContent = value + "px";
        }
        applyCardWidth(value);
        saveSize(value);
    });
}

function applySavedSize() {
    var renderer = getKanbanRenderer();
    if (!renderer) return;
    var value = getSavedSize();
    renderer.style.setProperty("--lens-card-width", value + "px");
    var slider = qs(".lensmemoriae-size-slider");
    if (slider) slider.value = value;
    var display = qs(".lensmemoriae-size-value");
    if (display) display.textContent = value + "px";
}

function ensureSizeBar() {
    var renderer = getKanbanRenderer();
    if (!renderer) return;

    if (!qs(".lensmemoriae-size-bar")) {
        var current = getSavedSize();
        var bar = document.createElement("div");
        bar.className = "lensmemoriae-size-bar";
        bar.innerHTML =
            '<label class="lensmemoriae-size-label">Mida:</label>' +
            '<input type="range" class="lensmemoriae-size-slider" min="120" max="400" step="10" value="' +
            current +
            '">' +
            '<span class="lensmemoriae-size-value">' +
            current +
            "px</span>";
        renderer.insertBefore(bar, renderer.firstChild);
    }
    applySavedSize();
}

var toolbarEl = null;

function openBulkTag(operation) {
    var ids = getSelectedIds();
    if (ids.length === 0) return;
    try {
        var actionService = registry.category("services").get("action");
        actionService.doAction({
            type: "ir.actions.act_window",
            name: operation === "add" ? "Add Tags" : "Remove Tags",
            res_model: "lensmemoriae.bulk.tag",
            view_mode: "form",
            target: "new",
            context: {
                default_operation: operation,
                default_image_ids: ids,
            },
        });
    } catch (_e) {
        /**/
    }
}

function clearSelection() {
    qsa(".lensmemoriae-kanban .o_kanban_record input[type='checkbox']:checked").forEach(
        function (cb) {
            cb.click();
        }
    );
}

function ensureToolbar() {
    if (toolbarEl) return;
    toolbarEl = document.createElement("div");
    toolbarEl.className = "lensmemoriae-bulk-toolbar";
    toolbarEl.innerHTML =
        '<span class="lensmemoriae-bulk-count"></span>' +
        '<div class="lensmemoriae-bulk-actions">' +
        '<button class="btn btn-sm btn-primary lensmemoriae-bulk-tag">' +
        '<i class="fa fa-tags"></i> Add Tag</button>' +
        '<button class="btn btn-sm btn-secondary lensmemoriae-bulk-untag">' +
        '<i class="fa fa-tag"></i> Remove Tag</button>' +
        '<button class="btn btn-sm btn-link lensmemoriae-bulk-clear">' +
        "Clear selection</button>" +
        "</div>";
    document.body.appendChild(toolbarEl);

    toolbarEl
        .querySelector(".lensmemoriae-bulk-tag")
        .addEventListener("click", function () {
            openBulkTag("add");
        });
    toolbarEl
        .querySelector(".lensmemoriae-bulk-untag")
        .addEventListener("click", function () {
            openBulkTag("remove");
        });
    toolbarEl
        .querySelector(".lensmemoriae-bulk-clear")
        .addEventListener("click", clearSelection);
}

function updateToolbar() {
    var ids = getSelectedIds();
    if (!toolbarEl) return;
    if (ids.length === 0) {
        toolbarEl.classList.remove("o_visible");
        return;
    }
    toolbarEl.classList.add("o_visible");
    toolbarEl.querySelector(".lensmemoriae-bulk-count").textContent =
        ids.length + " selected";
}

function observeSelection() {
    var kanban = qs(".lensmemoriae-kanban");
    if (!kanban) return;
    var renderer = kanban.querySelector(".o_kanban_renderer");
    if (!renderer) return;

    ensureToolbar();
    var observer = new MutationObserver(function () {
        updateToolbar();
    });
    observer.observe(renderer, {
        attributes: true,
        childList: true,
        subtree: true,
    });
}

function boot() {
    attachCinemaListeners();
    attachSizeListeners();

    if (qs(".lensmemoriae-kanban")) {
        ensureSizeBar();
        observeSelection();
        updateToolbar();
    }

    var observer = new MutationObserver(function () {
        var kanban = qs(".lensmemoriae-kanban");
        if (kanban) {
            ensureSizeBar();
            if (!toolbarEl) {
                observeSelection();
            }
            updateToolbar();
        }
    });
    observer.observe(document.body, {childList: true, subtree: true});
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
} else {
    boot();
}
