const API_BASE = "http://127.0.0.1:8000";

let latestSky = null;

const $ = (id) => document.getElementById(id);

function formatTime(value) {
    if (!value) return "--";

    return new Date(value).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit"
    });
}

function formatDate(value) {
    if (!value) return "Clemson University";

    return new Date(value).toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric"
    });
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function fetchSky() {
    const response = await fetch(`${API_BASE}/api/sky`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({})
    });

    if (!response.ok) {
        throw new Error(`Sky request failed (${response.status})`);
    }

    return response.json();
}

function renderSky(sky) {
    latestSky = sky;

    $("date-label").textContent =
        `${sky.location.name} • ${formatDate(sky.observed_at)}`;

    $("local-time").textContent =
        formatTime(sky.observed_at);

    const weather = sky.weather || {};
    $("sky-conditions").textContent =
        weather.available ? weather.summary : "Weather unavailable";

    const details = [];

    if (weather.temperature_c !== null && weather.temperature_c !== undefined) {
        details.push(`${Math.round(weather.temperature_c)}°C`);
    }

    if (weather.cloud_cover_percent !== null && weather.cloud_cover_percent !== undefined) {
        details.push(`${Math.round(weather.cloud_cover_percent)}% clouds`);
    }

    if (weather.wind_speed_kmh !== null && weather.wind_speed_kmh !== undefined) {
        details.push(`${Math.round(weather.wind_speed_kmh)} km/h wind`);
    }

    $("weather-details").textContent = details.join(" • ");
    $("observing-score").textContent = `${sky.observing_score}/100`;

    renderHighlights(sky.highlights || []);
    renderSkyMap(sky.objects || []);

    $("last-updated").textContent =
        `Last updated ${formatTime(sky.observed_at)}`;
}

function renderHighlights(highlights) {
    const container = $("highlights");

    if (!highlights.length) {
        container.innerHTML = `
            <p class="muted">
                No strong observing highlights are available right now.
            </p>
        `;
        return;
    }

    container.innerHTML = highlights.map((object) => `
        <article class="highlight-card" data-object-name="${escapeHtml(object.name)}">
            <div class="highlight-topline">
                <strong>${escapeHtml(object.name)}</strong>
                <span>${escapeHtml(object.direction)}</span>
            </div>
            <div class="highlight-meta">
                ${Number(object.altitude_deg).toFixed(1)}° altitude
            </div>
            <p>${escapeHtml(object.best_for)}</p>
            <small>${escapeHtml(object.educational_fact)}</small>
        </article>
    `).join("");

    container.querySelectorAll(".highlight-card").forEach((card) => {
        card.addEventListener("click", () => {
            const objectName = card.dataset.objectName;
            const object = highlights.find((item) => item.name === objectName);
            if (object) {
                loadGeminiOverview(object, latestSky);
            }
        });
    });
}

function renderSkyMap(objects) {
    const map = $("sky-map");

    map.querySelectorAll(".sky-object").forEach((node) => node.remove());

    const visible = objects.filter((object) => object.visible);

    if (!visible.length) {
        $("sky-message").textContent = "No visible targets right now.";
        $("sky-message").style.display = "block";
        return;
    }

    $("sky-message").style.display = "none";

    visible.forEach((object) => {
        const marker = document.createElement("button");
        marker.type = "button";
        marker.className = "sky-object";
        marker.title = `${object.name} • ${object.direction} • ${object.altitude_deg}°`;
        marker.innerHTML = `
            <span class="object-dot"></span>
            <span class="object-name">${escapeHtml(object.name)}</span>
        `;

        // Convert azimuth into a compass angle.
        // Convert altitude so horizon = outside and zenith = center.
        const angle = Number(object.azimuth_deg) * Math.PI / 180;
        const radius = Math.max(7, Math.min(43, 43 * (90 - Number(object.altitude_deg)) / 90));
        const x = 50 + radius * Math.sin(angle);
        const y = 50 - radius * Math.cos(angle);

        marker.style.left = `${x}%`;
        marker.style.top = `${y}%`;

        marker.addEventListener("click", () => {
            loadGeminiOverview(object, latestSky);
        });

        map.appendChild(marker);
    });
}

async function loadGeminiOverview(object, sky) {
    const output = $("gemini-overview");
    const target = $("gemini-target");
    const button = $("gemini-refresh");

    target.textContent = `${object.name} • ${object.direction} • ${object.altitude_deg}°`;
    output.textContent = "Gemini is thinking...";
    button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/explain`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                object_name: object.name,
                audience_level: "beginner",
                sky_context: {
                    location: sky.location.name,
                    observed_at: sky.observed_at,
                    altitude_deg: object.altitude_deg,
                    azimuth_deg: object.azimuth_deg,
                    direction: object.direction,
                    best_for: object.best_for,
                    educational_fact: object.educational_fact,
                    moon_phase: sky.moon_phase,
                    moon_illumination_percent: sky.moon_illumination_percent,
                    weather: sky.weather.summary
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Gemini request failed (${response.status})`);
        }

        const result = await response.json();
        output.textContent = result.text || "Gemini did not return an explanation.";
    } catch (error) {
        console.error(error);
        output.textContent =
            "Gemini is temporarily unavailable. The live sky data is still available.";
    } finally {
        button.disabled = false;
    }
}

async function refreshGemini() {
    if (!latestSky || !latestSky.highlights?.length) return;
    await loadGeminiOverview(latestSky.highlights[0], latestSky);
}

async function refreshEverything() {
    $("refresh-button").disabled = true;

    try {
        const sky = await fetchSky();
        renderSky(sky);

        if (sky.highlights?.length) {
            await loadGeminiOverview(sky.highlights[0], sky);
        } else {
            $("gemini-overview").textContent =
                "No strong observing target is available right now.";
        }
    } catch (error) {
        console.error(error);
        $("sky-conditions").textContent = "Backend unavailable";
        $("highlights").innerHTML = `
            <p class="error-message">
                Could not load sky data. Make sure the Python backend is running.
            </p>
        `;
        $("gemini-overview").textContent =
            "Start the backend and refresh the page.";
    } finally {
        $("refresh-button").disabled = false;
    }
}

$("refresh-button").addEventListener("click", refreshEverything);
$("gemini-refresh").addEventListener("click", refreshGemini);

refreshEverything();

// Keep the page live without making the user reload it.
setInterval(refreshEverything, 60000);
