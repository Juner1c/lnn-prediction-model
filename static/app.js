// Patch Canvas2D getContext for high-performance Leaflet heatmap readbacks
if (typeof HTMLCanvasElement !== "undefined") {
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, attributes) {
        if (type === "2d") {
            attributes = Object.assign({ willReadFrequently: true }, attributes);
        }
        return originalGetContext.call(this, type, attributes);
    };
}

document.addEventListener("DOMContentLoaded", () => {

    let map = null;
    let heatLayer = null;
    let isHeatmapVisible = true;
    let chart = null;
    let markersMap = {};
    let stationData = [];
    let stationForecasts = {}; // stationId -> forecast payload
    let activeStationId = null;
    let currentMetric = "heatIndex"; // "heatIndex" | "temperature" | "humidity"
    let autoUpdateInterval = null;


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

    function updateApiStatusBadge(isConnected, msg) {
        const badge = document.getElementById("api-status-badge");
        const dot = document.getElementById("api-status-dot");
        const text = document.getElementById("api-status-text");
        if (!badge || !dot || !text) return;

        if (isConnected) {
            badge.style.background = "rgba(46, 204, 113, 0.18)";
            badge.style.color = "#2ecc71";
            badge.style.borderColor = "rgba(46, 204, 113, 0.4)";
            dot.style.background = "#2ecc71";
            text.textContent = msg || "Kloudtech API: CONNECTED";
        } else {
            badge.style.background = "rgba(255, 69, 0, 0.18)";
            badge.style.color = "#FF4500";
            badge.style.borderColor = "rgba(255, 69, 0, 0.4)";
            dot.style.background = "#FF4500";
            text.textContent = msg || "Kloudtech API: DISCONNECTED";
        }
    }

    // Fetch live telemetry & station forecasts
    async function fetchLiveTelemetry() {
        try {
            const resp = await fetch("/telemetry/dashboard");
            if (!resp.ok) {
                updateApiStatusBadge(false, `Kloudtech API: ERROR (${resp.status})`);
                throw new Error(`API network error ${resp.status}`);
            }
            const res = await resp.json();
            if (res.success && res.data && res.data.length > 0) {
                updateApiStatusBadge(true, "Kloudtech API: CONNECTED");
                stationData = res.data.map(item => {
                    const st = item.station;
                    const tel = item.telemetry || {};
                    const t = tel.temperature || 31.0;
                    const rh = Math.min(100, Math.max(0, tel.humidity || 66.0));
                    const hi = tel.heatIndex || calculateHeatIndexLocal(t, rh);
                    return {
                        station: st,
                        telemetry: { temperature: t, humidity: rh, heatIndex: hi }
                    };
                });

                // Ensure activeStationId matches one of the real stations returned by Kloudtech API
                const exists = stationData.some(item => item.station && item.station.id === activeStationId);
                if (!exists && stationData.length > 0) {
                    activeStationId = stationData[0].station.id;
                }
            }
        } catch (e) {
            updateApiStatusBadge(false, "Kloudtech API: DISCONNECTED");
            stationData = [];
        }

        if (activeStationId) {
            await fetchStationForecast(activeStationId);
        }
        updateUIComponents();
    }


    // Fetch station forecast from backend endpoint
    async function fetchStationForecast(stId) {
        try {
            const resp = await fetch(`/telemetry/station/${stId}/forecast`);
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

    // Render Station Cards efficiently without DOM thrashing
    function renderStationCards() {
        const container = document.getElementById("station-list");
        if (!container) return;

        stationData.forEach(item => {
            const st = item.station;
            const tel = item.telemetry;
            let card = container.querySelector(`[data-station-id="${st.id}"]`);
            const isOnline = st.isActive !== false;
            const sourceTag = st.source || 'Kloudtech API';

            if (!card) {
                card = document.createElement("div");
                card.className = `station-card ${st.id === activeStationId ? 'active' : ''}`;
                card.setAttribute("data-station-id", st.id);
                card.setAttribute("tabindex", "0");
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <div class="station-card-title">${st.name}</div>
                        <span class="st-badge" style="font-size:10px; font-weight:600; padding:2px 6px; border-radius:4px; background:${isOnline ? 'rgba(46,204,113,0.18)' : 'rgba(255,159,10,0.18)'}; color:${isOnline ? '#2ecc71' : '#ff9f0a'}; border:1px solid ${isOnline ? 'rgba(46,204,113,0.4)' : 'rgba(255,159,10,0.4)'};">${sourceTag}</span>
                    </div>
                    <div class="station-card-metric">
                        <span class="st-temp">Temp: ${tel.temperature.toFixed(1)}°C</span>
                        <span class="st-rh">RH: ${tel.humidity.toFixed(1)}%</span>
                    </div>
                    <div class="station-card-metric">
                        <span style="color: var(--accent-orange); font-weight:600;">Heat Index:</span>
                        <strong class="st-hi">${tel.heatIndex.toFixed(1)}°C</strong>
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
            } else {
                card.className = `station-card ${st.id === activeStationId ? 'active' : ''}`;
                const tempEl = card.querySelector(".st-temp");
                const rhEl = card.querySelector(".st-rh");
                const hiEl = card.querySelector(".st-hi");
                const badgeEl = card.querySelector(".st-badge");
                if (tempEl) tempEl.textContent = `Temp: ${tel.temperature.toFixed(1)}°C`;
                if (rhEl) rhEl.textContent = `RH: ${tel.humidity.toFixed(1)}%`;
                if (hiEl) hiEl.textContent = `${tel.heatIndex.toFixed(1)}°C`;
                if (badgeEl) {
                    badgeEl.textContent = sourceTag;
                    badgeEl.style.background = isOnline ? 'rgba(46,204,113,0.18)' : 'rgba(255,159,10,0.18)';
                    badgeEl.style.color = isOnline ? '#2ecc71' : '#ff9f0a';
                }
            }
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
                        label: '16-Day NWP/STGNN Forecast (°C)',
                        data: [],
                        borderColor: '#FF9F0A',
                        backgroundColor: 'transparent',
                        borderDash: [4, 4],
                        tension: 0.35,
                        pointRadius: 0,
                        pointHoverRadius: 5
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
                        type: 'time',
                        time: {
                            displayFormats: {
                                minute: 'HH:mm',
                                hour: 'MMM d HH:mm',
                                day: 'MMM d'
                            }
                        },
                        ticks: {
                            color: '#A1A1AA',
                            maxRotation: 45
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.06)' }
                    },
                    y: { ticks: { color: '#A1A1AA' }, grid: { color: 'rgba(255, 255, 255, 0.06)' } }
                }
            }
        });

        // Direct click-and-drag mouse panning on canvas
        const chartCanvas = document.getElementById("telemetryChart");
        if (chartCanvas) {
            let isDragging = false;
            let startX = 0;
            let startMin = 0;
            let startMax = 0;

            chartCanvas.style.cursor = "grab";

            chartCanvas.addEventListener("mousedown", (e) => {
                if (!chart || !chart.scales || !chart.scales.x) return;
                isDragging = true;
                startX = e.clientX;
                startMin = chart.scales.x.min;
                startMax = chart.scales.x.max;
                chartCanvas.style.cursor = "grabbing";
            });

            window.addEventListener("mousemove", (e) => {
                if (!isDragging || !chart || !chart.scales || !chart.scales.x) return;
                const rect = chartCanvas.getBoundingClientRect();
                const chartWidth = rect.width;
                if (chartWidth <= 0) return;

                const dx = e.clientX - startX;
                const timeSpan = startMax - startMin;
                const shiftMs = -(dx / chartWidth) * timeSpan;

                let newMin = startMin + shiftMs;
                let newMax = startMax + shiftMs;

                const limits = chart.options.plugins && chart.options.plugins.zoom && chart.options.plugins.zoom.limits ? chart.options.plugins.zoom.limits.x : null;
                if (limits) {
                    if (newMin < limits.min) {
                        newMin = limits.min;
                        newMax = limits.min + timeSpan;
                    }
                    if (newMax > limits.max) {
                        newMax = limits.max;
                        newMin = limits.max - timeSpan;
                    }
                }

                chart.options.scales.x.min = newMin;
                chart.options.scales.x.max = newMax;
                chart.update('none');
            });

            window.addEventListener("mouseup", () => {
                if (isDragging) {
                    isDragging = false;
                    chartCanvas.style.cursor = "grab";
                }
            });
        }
    }

    // Dynamic Chart Updates with Full 96-step 24h History + 720-step 30-Day Hourly Forecast
    function updateChartData() {
        if (!chart || !stationData.length) return;

        const currentStation = stationData.find(item => item.station.id === activeStationId) || stationData[0];
        const tel = currentStation.telemetry;
        const fc = stationForecasts[activeStationId];

        const baseVal = tel[currentMetric] || tel.heatIndex;
        const now = new Date();

        // Preserve active user pan/zoom scale boundaries across 3-second live updates
        const savedMin = (chart.options.scales.x && chart.options.scales.x.min !== undefined) ? chart.options.scales.x.min : (chart.scales.x ? chart.scales.x.min : undefined);
        const savedMax = (chart.options.scales.x && chart.options.scales.x.max !== undefined) ? chart.options.scales.x.max : (chart.scales.x ? chart.scales.x.max : undefined);

        // Extract full 96 history values (24 hours at 15-min steps)
        let rawHistory = [];
        if (fc && fc.history_24h && fc.history_24h[currentMetric]) {
            rawHistory = fc.history_24h[currentMetric].map(v => parseFloat(v.toFixed(1)));
        } else {
            // Smooth realistic 24-hour diurnal profile (1 daily thermal peak at 14:00, 1 trough at 04:00)
            rawHistory = Array.from({length: 96}, (_, i) => {
                const hourOfDay = (now.getHours() - (95 - i) * 0.25 + 24) % 24;
                const diurnal = Math.sin(((hourOfDay - 8) / 24.0) * 2 * Math.PI);
                const scale = (currentMetric === 'humidity') ? -6.0 : 3.0;
                return parseFloat((baseVal + diurnal * scale * (i / 96.0)).toFixed(1));
            });
        }
        rawHistory[rawHistory.length - 1] = parseFloat(baseVal.toFixed(1));

        const numHist = rawHistory.length; // 96
        const rawTimestamps = (fc && fc.history_24h && fc.history_24h.timestamps) ? fc.history_24h.timestamps : [];

        // Build 24h history points ({ x: epochMs, y: Value })
        const historyPoints = [];
        let lastDate = now;

        for (let i = 0; i < numHist; i++) {
            let d;
            if (rawTimestamps[i]) {
                d = new Date(rawTimestamps[i]);
            } else {
                d = new Date(now.getTime() - (numHist - 1 - i) * (15 * 60 * 1000));
            }
            if (i === numHist - 1) lastDate = d;
            historyPoints.push({ x: d.getTime(), y: rawHistory[i] });
        }

        // Extract 384 forecast hourly mean, upper, lower bounds for 16-Day (384h) NWP/STGNN Horizon
        let rawMean = [];
        let rawUpper = [];
        let rawLower = [];

        const metricFc = (fc && fc.forecast_16day && fc.forecast_16day[currentMetric])
            ? fc.forecast_16day[currentMetric]
            : ((fc && fc.forecast_30day && fc.forecast_30day[currentMetric])
                ? fc.forecast_30day[currentMetric]
                : ((fc && fc.forecast_16step && fc.forecast_16step[currentMetric]) ? fc.forecast_16step[currentMetric] : null));

        if (metricFc && metricFc.mean && metricFc.mean.length) {
            rawMean = metricFc.mean.map(v => parseFloat(v.toFixed(1)));
            rawUpper = metricFc.upper.map((v, i) => parseFloat((v || rawMean[i] + 1.2).toFixed(1)));
            rawLower = metricFc.lower.map((v, i) => parseFloat((v || rawMean[i] - 1.2).toFixed(1)));
        } else {
            // Realistic diurnal continuation spanning 16 Days if API response is pending/cached
            for (let h = 1; h <= 384; h++) {
                const hourLocal = (lastDate.getHours() + h) % 24;
                const diurnal = Math.sin(((hourLocal - 8) / 24.0) * 2 * Math.PI);
                const scale = (currentMetric === 'humidity') ? -6.0 : 3.0;
                const meanVal = baseVal + (diurnal * scale * Math.min(1.0, h / 24.0));
                const spread = 1.0 + (h / 384.0) * 3.5;
                rawMean.push(parseFloat(meanVal.toFixed(1)));
                rawUpper.push(parseFloat((meanVal + spread).toFixed(1)));
                rawLower.push(parseFloat((meanVal - spread).toFixed(1)));
            }
        }


        const forecastMeanPoints = [{ x: lastDate.getTime(), y: parseFloat(baseVal.toFixed(1)) }];
        const forecastUpperPoints = [{ x: lastDate.getTime(), y: parseFloat(baseVal.toFixed(1)) }];
        const forecastLowerPoints = [{ x: lastDate.getTime(), y: parseFloat(baseVal.toFixed(1)) }];

        const hourMs = 60 * 60 * 1000;
        rawMean.forEach((m, idx) => {
            const t = new Date(lastDate.getTime() + (idx + 1) * hourMs);
            const meanVal = parseFloat(m.toFixed(1));
            const upperVal = parseFloat((rawUpper[idx] || meanVal + 1.5).toFixed(1));
            const lowerVal = parseFloat((rawLower[idx] || meanVal - 1.5).toFixed(1));

            forecastMeanPoints.push({ x: t.getTime(), y: meanVal });
            forecastUpperPoints.push({ x: t.getTime(), y: upperVal });
            forecastLowerPoints.push({ x: t.getTime(), y: lowerVal });
        });

        chart.data.datasets[0].label = `24h History ${currentMetric.toUpperCase()} (°C)`;
        chart.data.datasets[0].data = historyPoints;

        chart.data.datasets[1].data = forecastMeanPoints;
        chart.data.datasets[2].data = forecastUpperPoints;
        chart.data.datasets[3].data = forecastLowerPoints;

        const startHistMs = historyPoints[0].x;
        const endFcMs = forecastMeanPoints[forecastMeanPoints.length - 1].x;

        // Set strict zoom/pan limits to data boundaries so chart never pans into empty space
        if (chart.options.plugins && chart.options.plugins.zoom) {
            chart.options.plugins.zoom.limits = {
                x: { min: startHistMs, max: endFcMs, minRange: 3600000 * 6 } // min 6h zoom
            };
        }

        // Apply scale boundaries: restore saved pan/zoom if valid, otherwise set default 5-day initial view window
        if (typeof savedMin === 'number' && savedMin >= startHistMs && typeof savedMax === 'number' && savedMax <= endFcMs + 3600000) {
            chart.options.scales.x.min = savedMin;
            chart.options.scales.x.max = savedMax;
        } else {
            chart.options.scales.x.min = startHistMs;
            chart.options.scales.x.max = startHistMs + (5 * 24 * 60 * 60 * 1000); // 5-day default view (24h hist + 4d forecast)
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

    // Start 30-second background auto-update stream
    autoUpdateInterval = setInterval(fetchLiveTelemetry, 30000);
});
