/** @odoo-module **/

import {Component, useEffect, useRef, useState} from "@odoo/owl";
import {loadCSS, loadJS} from "@web/core/assets";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

const LEAFLET_VERSION = "1.9.4";
let leafletReady = null;

function ensureLeaflet() {
    if (!leafletReady) {
        leafletReady = Promise.all([
            loadJS(`https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.js`),
            loadCSS(`https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.css`),
        ]);
    }
    return leafletReady;
}

function nominatimSearch(query) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
    )}&limit=5`;
    return fetch(url, {
        headers: {"Accept-Language": "ca"},
    }).then((r) => r.json());
}

// ---------------------------------------------------------------------------
// Field widget: LeafletMapField (attached to latitude)
// ---------------------------------------------------------------------------

export class LeafletMapField extends Component {
    static template = "lensmemoriae.LeafletMapField";
    static props = {...standardFieldProps};

    setup() {
        this.state = useState({
            lat: this.props.record.data.latitude,
            lng: this.props.record.data.longitude,
            loading: true,
            searchQuery: "",
            searchResults: null,
            searching: false,
        });
        this.mapRef = useRef("mapContainer");
        this.leafletMap = null;
        this.marker = null;
        this.ready = false;

        useEffect(
            () => {
                ensureLeaflet().then(() => {
                    this.ready = true;
                    this.initMap();
                });
                return () => this.destroyMap();
            },
            () => []
        );

        useEffect(
            (lat, lng) => {
                this.state.lat = lat;
                this.state.lng = lng;
                if (this.ready) {
                    this.updateMarker(lat, lng);
                }
            },
            () => [this.props.record.data.latitude, this.props.record.data.longitude]
        );
    }

    get defaultCenter() {
        return {lat: 41.5526, lng: 2.4002};
    }

    initMap() {
        const container = this.mapRef.el;
        if (!container) return;

        const lat = this.state.lat || this.defaultCenter.lat;
        const lng = this.state.lng || this.defaultCenter.lng;
        this.state.loading = false;

        this.leafletMap = L.map(container, {
            zoom: this.state.lat ? 15 : 6,
            center: [lat, lng],
            attributionControl: false,
        });
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution:
                '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(this.leafletMap);

        if (this.state.lat && this.state.lng) {
            this.createMarker(this.state.lat, this.state.lng);
        }

        if (!this.props.readonly) {
            this.leafletMap.on("click", (ev) => {
                this.setLocation(ev.latlng.lat, ev.latlng.lng);
            });
        }

        setTimeout(() => this.leafletMap.invalidateSize(), 100);
    }

    createMarker(lat, lng) {
        if (this.marker) {
            this.marker.setLatLng([lat, lng]);
            return;
        }
        this.marker = L.marker([lat, lng], {
            draggable: !this.props.readonly,
        }).addTo(this.leafletMap);

        if (!this.props.readonly) {
            this.marker.on("dragend", (ev) => {
                const pos = ev.target.getLatLng();
                this.setLocation(pos.lat, pos.lng);
            });
        }
    }

    updateMarker(lat, lng) {
        if (this.marker) {
            this.marker.setLatLng([lat, lng]);
        } else if (lat && lng) {
            this.createMarker(lat, lng);
        }
    }

    destroyMap() {
        if (this.leafletMap) {
            this.leafletMap.remove();
            this.leafletMap = null;
            this.marker = null;
        }
    }

    setLocation(lat, lng) {
        const roundedLat = Math.round(lat * 1e6) / 1e6;
        const roundedLng = Math.round(lng * 1e6) / 1e6;
        this.state.lat = roundedLat;
        this.state.lng = roundedLng;
        this.props.record.update({
            latitude: roundedLat,
            longitude: roundedLng,
        });
        this.createMarker(roundedLat, roundedLng);
        this.leafletMap.setView([roundedLat, roundedLng], 15, {
            animate: true,
        });
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
        if (!ev.target.value.trim()) {
            this.state.searchResults = null;
        }
    }

    onSearch(ev) {
        ev.preventDefault();
        const query = this.state.searchQuery;
        if (!query || !query.trim()) return;
        this.state.searching = true;
        this.state.searchResults = null;
        nominatimSearch(query.trim())
            .then((results) => {
                this.state.searchResults = results;
                this.state.searching = false;
            })
            .catch(() => {
                this.state.searching = false;
            });
    }

    onSelectResult(result) {
        const lat = parseFloat(result.lat);
        const lng = parseFloat(result.lon);
        this.state.searchResults = null;
        this.state.searchQuery = result.display_name;
        this.setLocation(lat, lng);
    }
}

export const leafletMapField = {
    component: LeafletMapField,
    displayName: "Leaflet Map",
    supportedTypes: ["float"],
    fieldDependencies: [{name: "longitude", type: "float"}],
    isEmpty: (record) => !record.data.latitude || !record.data.longitude,
};

registry.category("fields").add("leaflet_map", leafletMapField);

// ---------------------------------------------------------------------------
// Client action: LensMemoriae Map View (full-screen map with all markers)
// ---------------------------------------------------------------------------

class LensMemoriaeMapView extends Component {
    static template = "lensmemoriae.MapView";

    setup() {
        this.state = useState({
            markers: [],
            loading: true,
        });
        this.mapRef = useRef("mapContainer");
        this.leafletMap = null;
        this.markerLayer = null;
        this.orm = useService("orm");

        this.loadData();
    }

    async loadData() {
        try {
            const images = await this.orm.searchRead(
                "lensmemoriae.image",
                [
                    ["latitude", "!=", false],
                    ["longitude", "!=", false],
                ],
                ["id", "name", "latitude", "longitude", "image"],
                {order: "name"}
            );
            this.state.markers = images;
        } catch (e) {
            // Silent
        } finally {
            this.state.loading = false;
            this.initMap();
        }
    }

    initMap() {
        ensureLeaflet().then(() => {
            const container = this.mapRef.el;
            if (!container) return;

            this.leafletMap = L.map(container, {
                zoom: 6,
                center: [41.5526, 2.4002],
                attributionControl: false,
            });
            L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution:
                    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            }).addTo(this.leafletMap);

            this.addMarkers();
            setTimeout(() => this.leafletMap.invalidateSize(), 100);
        });
    }

    addMarkers() {
        if (!this.leafletMap) return;
        if (this.markerLayer) {
            this.leafletMap.removeLayer(this.markerLayer);
        }

        const markers = this.state.markers.map((img) => {
            const marker = L.marker([img.latitude, img.longitude]);
            const thumbnail = img.image ? `data:image/png;base64,${img.image}` : "";
            const popupContent = `
                <div style="min-width:180px;text-align:center;">
                    ${
                        thumbnail
                            ? `<img src="${thumbnail}" style="max-width:150px;max-height:120px;object-fit:contain;margin-bottom:4px;border-radius:3px;" />`
                            : ""
                    }
                    <br/>
                    <strong>${img.name}</strong>
                    <br/>
                    <a href="/web#id=${img.id}&model=lensmemoriae.image&view_type=form"
                       style="font-size:12px;" target="_blank">
                        Open record
                    </a>
                </div>`;
            marker.bindPopup(popupContent);
            return marker;
        });

        this.markerLayer = L.layerGroup(markers).addTo(this.leafletMap);

        if (markers.length) {
            const group = L.featureGroup(markers);
            this.leafletMap.fitBounds(group.getBounds().pad(0.1));
        }
    }

    onFitAll() {
        if (this.markerLayer) {
            const markers = this.markerLayer.getLayers();
            if (markers.length) {
                const group = L.featureGroup(markers);
                this.leafletMap.fitBounds(group.getBounds().pad(0.1));
            }
        }
    }
}

registry.category("actions").add("lensmemoriae.map_view", LensMemoriaeMapView);
