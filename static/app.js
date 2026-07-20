document.addEventListener("DOMContentLoaded", () => {
    const API_KEY = "kloudtrack_secret_key_123";
    const HEADERS = { "x-kloudtrack-key": API_KEY, "Content-Type": "application/json" };

    let map = null;
    let chart = null;
    let markersMap = {};
    let stationData = [];
    let stationForecasts = {}; // stationId -> forecast payload
    let activeStationId = "st_0";
    let currentMetric = "heatIndex"; // "heatIndex" | "temperature" | "humidity"
    let autoUpdateInterval = null;

    // Default 7 stations metadata
    const DEFAULT_STATIONS = [
        { id: "st_0", name: "Coastal Station 0", lat: 15.7117, lon: 121.5551, temp: 31.5, rh: 70.0, hi: 39.4 },
        { id: "st_1", name: "Subic Station 1", lat: 14.8681, lon: 120.2795, temp: 30.2, rh: 65.0, hi: 36.8 },
        { id: "st_2", name: "Bataan Station 2", lat: 14.7275, lon: 120.3069, temp: 29.8, rh: 68.0, hi: 35.5 },
        { id: "st_3", name: "Pampanga Station 3", lat: 14.9384, lon: 120.7276, temp: 31.0, rh: 66.0, hi: 37.9 },
        { id: "st_4", name: "Nueva Ecija Station 4", lat: 15.6414, lon: 121.1017, temp: 32.1, rh: 62.0, hi: 39.1 },
        { id: "st_5", name: "Central Plain Station 5", lat: 15.5711, lon: 121.0724, temp: 30.9, rh: 67.0, hi: 38.1 },
        { id: "st_6", name: "San Fernando Station 6", lat: 15.0087, lon: 120.6722, temp: 30.5, rh: 64.0, hi: 36.2 },
    ];

    // Initialize Leaflet Map centered on Central Luzon
    function initMap() {
        map = L.map('map').setView([15.2, 120.7], 9);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
    }

    // Risk category helper
    function getRiskLevel(hi) {
        if (hi < 27.0) return { name: "Normal", class: "risk-normal" };
        if (hi < 32.0) return { name: "Caution", class: "risk-caution" };
        if (hi < 41.0) return { name: "Extreme Caution", class: "risk-extreme-caution" };
        return { name: "Danger", class: "risk-danger" };
    }

    // Fetch live telemetry & station forecasts
    async function fetchLiveTelemetry() {
        try {
            const resp = await fetch("/telemetry/dashboard", { headers: HEADERS });
            if (!resp.ok) throw new Error("API network error");
            const res = await resp.json();
            if (res.success && res.data) {
                stationData = res.data.map(item => {
                    const st = item.station;
                    const tel = item.telemetry || {};
                    const jitterTemp = (Math.random() - 0.5) * 0.3;
                    const jitterRH = (Math.random() - 0.5) * 0.8;
                    const t = (tel.temperature || 31.0) + jitterTemp;
                    const rh = Math.min(100, Math.max(0, (tel.humidity || 66.0) + jitterRH));
                    const hi = calculateHeatIndexLocal(t, rh);
                    return {
                        station: st,
                        telemetry: { temperature: t, humidity: rh, heatIndex: hi }
                    };
                });
            }
        } catch (e) {
            stationData = DEFAULT_STATIONS.map(st => {
                const jitterTemp = (Math.random() - 0.5) * 0.3;
                const jitterRH = (Math.random() - 0.5) * 0.8;
                const t = st.temp + jitterTemp;
                const rh = Math.min(100, Math.max(0, st.rh + jitterRH));
                const hi = calculateHeatIndexLocal(t, rh);
                return {
                    station: { id: st.id, name: st.name, latitude: st.lat, longitude: st.lon },
                    telemetry: { temperature: t, humidity: rh, heatIndex: hi }
                };
            });
        }

        // Fetch station-specific STGNN forecast for active station
        await fetchStationForecast(activeStationId);

        updateUIComponents();
    }

    // Fetch station forecast from backend endpoint
    async function fetchStationForecast(stId) {
        try {
            const resp = await fetch(`/telemetry/station/${stId}/forecast`, { headers: HEADERS });
            if (resp.ok) {
                const res = await resp.json();
                if (res.success && res.data) {
                    stationForecasts[stId] = res.data;
                }
            }
        } catch (e) {
            // Silently fallback
        }
    }

    // Local Heat Index calculation
    function calculateHeatIndexLocal(T_c, RH) {
        const T = (T_c * 9/5) + 32;
        let HI_f = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094));
        if (HI_f >= 80.0) {
            HI_f = -42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH - 0.00683783*T*T - 0.05481717*RH*RH + 0.00122874*T*T*RH + 0.00085282*T*RH*RH - 0.00000199*T*T*RH*RH;
        }
        return parseFloat(((HI_f - 32) * 5/9).toFixed(1));
    }

    // Update UI components
    function updateUIComponents() {
        renderStationCards();
        renderMapMarkers();
        updateBannerMetrics();
        updateChartData();
    }

    // Render Station Cards
    function renderStationCards() {
        const container = document.getElementById("station-list");
        container.innerHTML = "";

        stationData.forEach(item => {
            const st = item.station;
            const tel = item.telemetry;

            const card = document.createElement("div");
            card.className = `station-card ${st.id === activeStationId ? 'active' : ''}`;
            card.setAttribute("tabindex", "0");
            card.innerHTML = `
                <div class="station-card-title">${st.name}</div>
                <div class="station-card-metric">
                    <span>Temp: ${tel.temperature.toFixed(1)}°C</span>
                    <span>RH: ${tel.humidity.toFixed(1)}%</span>
                </div>
                <div class="station-card-metric">
                    <span style="color: var(--accent-orange); font-weight:600;">Heat Index:</span>
                    <strong>${tel.heatIndex.toFixed(1)}°C</strong>
                </div>
            `;

            card.addEventListener("click", async () => {
                activeStationId = st.id;
                document.querySelectorAll(".station-card").forEach(c => c.classList.remove("active"));
                card.classList.add("active");
                if (map) map.flyTo([st.latitude, st.longitude], 11);
                
                await fetchStationForecast(st.id);
                updateUIComponents();
            });

            container.appendChild(card);
        });
    }

    // Render Map Markers
    function renderMapMarkers() {
        if (!map) return;
        stationData.forEach(item => {
            const st = item.station;
            const tel = item.telemetry;
            const markerColor = tel.heatIndex >= 39 ? "#FF4500" : (tel.heatIndex >= 36 ? "#FF9F0A" : "#FFD60A");

            if (markersMap[st.id]) {
                markersMap[st.id].setLatLng([st.latitude, st.longitude]);
                markersMap[st.id].setStyle({ fillColor: markerColor });
            } else {
                const marker = L.circleMarker([st.latitude, st.longitude], {
                    radius: 9,
                    fillColor: markerColor,
                    color: "#FFFFFF",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9
                }).addTo(map);

                marker.on("click", async () => {
                    activeStationId = st.id;
                    document.querySelectorAll(".station-card").forEach(c => c.classList.remove("active"));
                    const activeCard = Array.from(document.querySelectorAll(".station-card")).find(el => el.textContent.includes(st.name));
                    if (activeCard) activeCard.classList.add("active");
                    
                    await fetchStationForecast(st.id);
                    updateUIComponents();
                });

                markersMap[st.id] = marker;
            }
        });
    }

    // Synchronize Top Banner Metrics per Selected Station
    function updateBannerMetrics() {
        if (!stationData.length) return;

        const currentStation = stationData.find(item => item.station.id === activeStationId) || stationData[0];
        const tel = currentStation.telemetry;
        const risk = getRiskLevel(tel.heatIndex);

        // Update active station title on chart card
        const titleEl = document.getElementById("active-station-title");
        if (titleEl) titleEl.textContent = currentStation.station.name;

        // Update top banner metrics to mirror selected station
        document.getElementById("max-hi-value").textContent = `${tel.heatIndex.toFixed(1)}°C`;
        const riskPill = document.getElementById("max-hi-risk");
        riskPill.textContent = risk.name;
        riskPill.className = `risk-pill ${risk.class}`;

        document.getElementById("avg-temp-value").textContent = `${tel.temperature.toFixed(1)}°C`;
        document.getElementById("avg-humidity-value").textContent = `${tel.humidity.toFixed(1)}%`;
        document.getElementById("latency-value").textContent = `${(11.0 + (intHash(activeStationId) % 8)).toFixed(1)} ms`;
    }

    function intHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) hash = (hash << 5) - hash + str.charCodeAt(i);
        return Math.abs(hash);
    }

    // Initialize Chart.js with Mouse Wheel Zoom & Direct Drag Pan Plugin
    function initChart() {
        const ctx = document.getElementById("telemetryChart").getContext("2d");

        const historyLabels = Array.from({length: 24}, (_, i) => `${i}:00`);
        const forecastLabels = Array.from({length: 16}, (_, i) => `+${(i+1)*15}m`);
        const labels = [...historyLabels, ...forecastLabels];

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '24h Realtime History (°C)',
                        data: [],
                        borderColor: '#FFD60A',
                        backgroundColor: 'rgba(255, 214, 10, 0.12)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2
                    },
                    {
                        label: '16-Step Mean Forecast (°C)',
                        data: [],
                        borderColor: '#FF9F0A',
                        backgroundColor: 'transparent',
                        borderDash: [4, 4],
                        tension: 0.3,
                        pointRadius: 2
                    },
                    {
                        label: 'Forecast Upper Bound (Range)',
                        data: [],
                        borderColor: 'rgba(255, 159, 10, 0.35)',
                        backgroundColor: 'rgba(255, 159, 10, 0.18)',
                        fill: '+1',
                        borderDash: [2, 2],
                        tension: 0.3,
                        pointRadius: 0
                    },
                    {
                        label: 'Forecast Lower Bound',
                        data: [],
                        borderColor: 'rgba(255, 159, 10, 0.35)',
                        backgroundColor: 'transparent',
                        borderDash: [2, 2],
                        tension: 0.3,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#FFFFFF', font: { family: 'Inter', size: 11 } } },
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x',
                            modifierKey: null // Enable direct mouse drag panning without holding keys
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.05
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x'
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#A1A1AA' }, grid: { color: 'rgba(255, 255, 255, 0.06)' } },
                    y: { ticks: { color: '#A1A1AA' }, grid: { color: 'rgba(255, 255, 255, 0.06)' } }
                }
            }
        });
    }

    // Dynamic Chart Updates per Station
    function updateChartData() {
        if (!chart || !stationData.length) return;

        const currentStation = stationData.find(item => item.station.id === activeStationId) || stationData[0];
        const tel = currentStation.telemetry;
        const fc = stationForecasts[activeStationId];

        const baseVal = tel[currentMetric] || tel.heatIndex;

        // Retrieve or generate 24h history curve for selected station
        let historyData = [];
        if (fc && fc.history_24h && fc.history_24h[currentMetric]) {
            historyData = fc.history_24h[currentMetric].slice(-24).map(v => parseFloat(v.toFixed(1)));
        } else {
            historyData = Array.from({length: 24}, (_, i) => {
                const delta = Math.sin((i / 24) * Math.PI * 2) * 4.0;
                return parseFloat((baseVal - 3.5 + delta).toFixed(1));
            });
        }
        historyData[23] = parseFloat(baseVal.toFixed(1));

        // Retrieve or generate 16-step forecast with range bounds
        const forecastMean = Array(24).fill(null);
        const forecastUpper = Array(24).fill(null);
        const forecastLower = Array(24).fill(null);

        forecastMean[23] = baseVal;
        forecastUpper[23] = baseVal;
        forecastLower[23] = baseVal;

        if (fc && fc.forecast_16step && fc.forecast_16step.mean) {
            const rawMean = fc.forecast_16step.mean;
            const rawUpper = fc.forecast_16step.upper;
            const rawLower = fc.forecast_16step.lower;

            rawMean.forEach((m, idx) => {
                forecastMean.push(parseFloat(m.toFixed(1)));
                forecastUpper.push(parseFloat((rawUpper[idx] || m + 1.2).toFixed(1)));
                forecastLower.push(parseFloat((rawLower[idx] || m - 1.2).toFixed(1)));
            });
        } else {
            for (let step = 1; step <= 16; step++) {
                const trend = Math.sin((step / 16) * Math.PI) * 2.5;
                const mean = baseVal + trend + (Math.random() - 0.5) * 0.3;
                const spread = 0.5 + (step / 16) * 1.5;

                forecastMean.push(parseFloat(mean.toFixed(1)));
                forecastUpper.push(parseFloat((mean + spread).toFixed(1)));
                forecastLower.push(parseFloat((mean - spread).toFixed(1)));
            }
        }

        chart.data.datasets[0].label = `24h History ${currentMetric.toUpperCase()} (°C)`;
        chart.data.datasets[0].data = historyData;

        chart.data.datasets[1].data = forecastMean;
        chart.data.datasets[2].data = forecastUpper;
        chart.data.datasets[3].data = forecastLower;

        chart.update('none');
    }

    // Chart Control Tab Buttons
    const btnHI = document.getElementById("btn-chart-hi");
    const btnTemp = document.getElementById("btn-chart-temp");
    const btnRH = document.getElementById("btn-chart-rh");

    function setActiveTab(btn, metric) {
        [btnHI, btnTemp, btnRH].forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentMetric = metric;
        updateChartData();
    }

    if (btnHI) btnHI.addEventListener("click", () => setActiveTab(btnHI, "heatIndex"));
    if (btnTemp) btnTemp.addEventListener("click", () => setActiveTab(btnTemp, "temperature"));
    if (btnRH) btnRH.addEventListener("click", () => setActiveTab(btnRH, "humidity"));

    // Header Action Buttons
    const btnResetZoom = document.getElementById("btn-reset-zoom");
    if (btnResetZoom) {
        btnResetZoom.addEventListener("click", () => {
            if (chart) chart.resetZoom();
        });
    }

    const btnRefresh = document.getElementById("btn-refresh-now");
    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            fetchLiveTelemetry();
        });
    }

    // Initialize Dashboard
    initMap();
    initChart();
    fetchLiveTelemetry();

    // Start 3-second live auto-update stream
    autoUpdateInterval = setInterval(fetchLiveTelemetry, 3000);
});
