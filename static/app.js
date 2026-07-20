document.addEventListener("DOMContentLoaded", () => {
    const API_KEY = "kloudtrack_secret_key_123";
    const HEADERS = { "x-kloudtrack-key": API_KEY, "Content-Type": "application/json" };

    let map = null;
    let heatLayer = null;
    let isHeatmapVisible = true;
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

    // Calculate Inverse Distance Weighting (IDW) spatial interpolation
    function renderIDWHeatmap() {
        if (!map || !window.L || !L.heatLayer || !stationData.length) return;

        const gridPoints = [];
        const lats = stationData.map(d => d.station.latitude);
        const lons = stationData.map(d => d.station.longitude);

        const minLat = Math.min(...lats) - 0.2;
        const maxLat = Math.max(...lats) + 0.2;
        const minLon = Math.min(...lons) - 0.2;
        const maxLon = Math.max(...lons) + 0.2;

        const step = 0.04; // ~4km grid step

        for (let lat = minLat; lat <= maxLat; lat += step) {
            for (let lon = minLon; lon <= maxLon; lon += step) {
                let weightSum = 0;
                let valSum = 0;

                stationData.forEach(item => {
                    const d = haversine(lat, lon, item.station.latitude, item.station.longitude);
                    const w = 1 / Math.pow(Math.max(d, 0.5), 2); // IDW power p=2
                    weightSum += w;
                    valSum += w * item.telemetry.heatIndex;
                });

                const interpHI = valSum / weightSum;
                const normalizedIntensity = Math.min(1.0, Math.max(0.1, (interpHI - 25.0) / 20.0));
                gridPoints.push([lat, lon, normalizedIntensity]);
            }
        }

        if (heatLayer) map.removeLayer(heatLayer);

        if (isHeatmapVisible) {
            heatLayer = L.heatLayer(gridPoints, {
                radius: 25,
                blur: 18,
                maxZoom: 14,
                gradient: { 0.3: '#FFD60A', 0.65: '#FF9F0A', 1.0: '#FF4500' }
            }).addTo(map);
        }
    }

    function haversine(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    // Heat Vulnerability Index (HVI) calculation formula
    function calculateHVI(hi, temp, rh) {
        const normHI = Math.min(1.0, Math.max(0.0, (hi - 20.0) / 35.0));
        const normTemp = Math.min(1.0, Math.max(0.0, (temp - 20.0) / 25.0));
        const normRH = Math.min(1.0, Math.max(0.0, rh / 100.0));
        const hvi = (0.5 * normHI) + (0.3 * normTemp) + (0.2 * normRH);
        return parseFloat(hvi.toFixed(2));
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
            // Fallback
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
        renderIDWHeatmap();
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
                    fillOpacity: 0.95
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
        const hvi = calculateHVI(tel.heatIndex, tel.temperature, tel.humidity);

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
        document.getElementById("hvi-value").textContent = `${hvi} (High)`;
    }

    // Initialize Chart.js with Clean Category Time Scale & Zoom/Pan Support
    function initChart() {
        const ctx = document.getElementById("telemetryChart").getContext("2d");

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '24h History (°C)',
                        data: [],
                        borderColor: '#FFD60A',
                        backgroundColor: 'rgba(255, 214, 10, 0.12)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2
                    },
                    {
                        label: '16-Day Mean Forecast (°C)',
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
                            modifierKey: null,
                            threshold: 0
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
                    x: {
                        ticks: {
                            color: '#A1A1AA',
                            maxRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 20
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.06)' }
                    },
                    y: { ticks: { color: '#A1A1AA' }, grid: { color: 'rgba(255, 255, 255, 0.06)' } }
                }
            }
        });
    }

    // Helper to format Date objects as HH:mm
    function formatTime(d) {
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    // Dynamic Chart Updates with Full 96-step 24h History + 16-step Future Forecast
    function updateChartData() {
        if (!chart || !stationData.length) return;

        const currentStation = stationData.find(item => item.station.id === activeStationId) || stationData[0];
        const tel = currentStation.telemetry;
        const fc = stationForecasts[activeStationId];

        const baseVal = tel[currentMetric] || tel.heatIndex;
        const now = new Date();
        const stepMs = 15 * 60 * 1000; // 15-minute interval

        // Preserve active user pan/zoom scale boundaries across 3-second live updates
        const savedMin = (chart.options.scales.x && chart.options.scales.x.min !== undefined) ? chart.options.scales.x.min : (chart.scales.x ? chart.scales.x.min : undefined);
        const savedMax = (chart.options.scales.x && chart.options.scales.x.max !== undefined) ? chart.options.scales.x.max : (chart.scales.x ? chart.scales.x.max : undefined);

        // Extract full 96 history values (24 hours at 15-min steps)
        let rawHistory = [];
        if (fc && fc.history_24h && fc.history_24h[currentMetric]) {
            rawHistory = fc.history_24h[currentMetric].map(v => parseFloat(v.toFixed(1)));
        } else {
            rawHistory = Array.from({length: 96}, (_, i) => {
                const delta = Math.sin((i / 96) * Math.PI * 4) * 3.5;
                return parseFloat((baseVal - 3.0 + delta).toFixed(1));
            });
        }
        rawHistory[rawHistory.length - 1] = parseFloat(baseVal.toFixed(1));

        const numHist = rawHistory.length; // 96
        const rawTimestamps = (fc && fc.history_24h && fc.history_24h.timestamps) ? fc.history_24h.timestamps : [];

        // Build continuous timeline labels from actual PHT timestamps
        const timeLabels = [];
        let lastDate = now;

        for (let i = 0; i < numHist; i++) {
            if (rawTimestamps[i]) {
                const d = new Date(rawTimestamps[i]);
                timeLabels.push(formatTime(d));
                if (i === numHist - 1) lastDate = d;
            } else {
                const t = new Date(now.getTime() - (numHist - 1 - i) * stepMs);
                timeLabels.push(formatTime(t));
                if (i === numHist - 1) lastDate = t;
            }
        }

        // Add 16 daily forecast step labels into the future (16 Days horizon)
        const dayMs = 24 * 60 * 60 * 1000;
        for (let step = 1; step <= 16; step++) {
            const t = new Date(lastDate.getTime() + step * dayMs);
            const dateStr = t.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            timeLabels.push(`Day +${step} (${dateStr})`);
        }

        // Dataset 0: History (96 values followed by nulls for forecast window)
        const historyData = [...rawHistory, ...Array(16).fill(null)];

        // Extract 16 forecast mean, upper, lower bounds for the active metric
        let rawMean = [];
        let rawUpper = [];
        let rawLower = [];

        const metricFc = (fc && fc.forecast_16step && fc.forecast_16step[currentMetric])
            ? fc.forecast_16step[currentMetric]
            : (fc && fc.forecast_16step ? fc.forecast_16step : null);

        if (metricFc && metricFc.mean) {
            rawMean = metricFc.mean.map(v => parseFloat(v.toFixed(1)));
            rawUpper = metricFc.upper.map((v, i) => parseFloat((v || rawMean[i] + 1.2).toFixed(1)));
            rawLower = metricFc.lower.map((v, i) => parseFloat((v || rawMean[i] - 1.2).toFixed(1)));
        } else {
            for (let step = 1; step <= 16; step++) {
                const trend = Math.sin((step / 16) * Math.PI) * 2.5;
                const mean = baseVal + trend + (Math.random() - 0.5) * 0.3;
                const spread = 0.5 + (step / 16) * 1.5;
                rawMean.push(parseFloat(mean.toFixed(1)));
                rawUpper.push(parseFloat((mean + spread).toFixed(1)));
                rawLower.push(parseFloat((mean - spread).toFixed(1)));
            }
        }

        // Forecast datasets start at index 95 (Now) so lines connect smoothly
        const forecastMeanData = [...Array(numHist - 1).fill(null), parseFloat(baseVal.toFixed(1)), ...rawMean];
        const forecastUpperData = [...Array(numHist - 1).fill(null), parseFloat(baseVal.toFixed(1)), ...rawUpper];
        const forecastLowerData = [...Array(numHist - 1).fill(null), parseFloat(baseVal.toFixed(1)), ...rawLower];

        chart.data.labels = timeLabels;
        chart.data.datasets[0].label = `24h History ${currentMetric.toUpperCase()} (°C)`;
        chart.data.datasets[0].data = historyData;

        chart.data.datasets[1].data = forecastMeanData;
        chart.data.datasets[2].data = forecastUpperData;
        chart.data.datasets[3].data = forecastLowerData;

        if (savedMin !== undefined && savedMax !== undefined) {
            chart.options.scales.x.min = savedMin;
            chart.options.scales.x.max = savedMax;
        }

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

    // Heatmap Overlay Toggle Button
    const btnToggleHeatmap = document.getElementById("btn-toggle-heatmap");
    if (btnToggleHeatmap) {
        btnToggleHeatmap.addEventListener("click", () => {
            isHeatmapVisible = !isHeatmapVisible;
            btnToggleHeatmap.textContent = isHeatmapVisible ? "Heatmap Overlay: ON" : "Heatmap Overlay: OFF";
            btnToggleHeatmap.classList.toggle("active-toggle", isHeatmapVisible);
            renderIDWHeatmap();
        });
    }

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
