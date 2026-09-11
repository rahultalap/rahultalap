/* =========================================================
   COALGUARD AI - FRONTEND JAVASCRIPT
   Connects Frontend -> FastAPI -> Supabase
========================================================= */

const API_BASE = window.location.origin;

let currentUser = null;
let currentMineId = 1;
let currentMine = null;

let miniMap = null;
let fullMap = null;


/* =========================================================
   HELPER FUNCTIONS
========================================================= */

async function apiRequest(url, options = {}) {

    try {

        const response = await fetch(API_BASE + url, {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Request failed");
        }

        return data;

    } catch (error) {

        console.error("API Error:", error);

        showToast("Backend connection error");

        throw error;
    }
}


/* =========================================================
   TOAST
========================================================= */

function showToast(message) {

    const toast = document.getElementById("toast");

    if (!toast) return;

    toast.textContent = message;

    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}


/* =========================================================
   LOGIN
========================================================= */

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const email =
            document.getElementById("email").value.trim();

        const password =
            document.getElementById("password").value;

        try {

            const data = await apiRequest("/api/auth/login", {

                method: "POST",

                body: JSON.stringify({
                    email: email,
                    password: password
                })

            });

            currentUser = data.user;

            currentMineId = data.user.mine_id;

            localStorage.setItem(
                "coalguard_user",
                JSON.stringify(currentUser)
            );

            document.getElementById("loginView")
                .classList.add("hidden");

            document.getElementById("appView")
                .classList.remove("hidden");

            updateUserInformation();

            await loadMine();

            await loadDashboardData();

            initializeMaps();

            showToast("Welcome to CoalGuard AI");

        } catch (error) {

            console.error(error);

        }

    });
}


/* =========================================================
   RESTORE LOGIN
========================================================= */

window.addEventListener("DOMContentLoaded", async () => {

    const savedUser =
        localStorage.getItem("coalguard_user");

    if (savedUser) {

        try {

            currentUser = JSON.parse(savedUser);

            currentMineId =
                currentUser.mine_id || 1;

            document.getElementById("loginView")
                .classList.add("hidden");

            document.getElementById("appView")
                .classList.remove("hidden");

            updateUserInformation();

            await loadMine();

            await loadDashboardData();

            initializeMaps();

        } catch (error) {

            console.error(error);

            localStorage.removeItem("coalguard_user");
        }
    }

});


/* =========================================================
   USER INFORMATION
========================================================= */

function updateUserInformation() {

    if (!currentUser) return;

    const userName =
        document.getElementById("userName");

    const userRole =
        document.getElementById("userRole");

    const avatar =
        document.getElementById("avatar");

    if (userName) {
        userName.textContent =
            currentUser.name;
    }

    if (userRole) {
        userRole.textContent =
            currentUser.role;
    }
    const greeting = document.getElementById("greeting");

if (greeting) {
    const firstName = currentUser.name.split(" ")[0];
    greeting.textContent = `Hello , ${firstName}.`;
}


    if (avatar) {

        const nameParts =
            currentUser.name.split(" ");

        const initials =
            nameParts
                .map(part => part[0])
                .join("")
                .substring(0, 2)
                .toUpperCase();

        avatar.textContent = initials;
    }

}


/* =========================================================
   LOGOUT
========================================================= */

const logoutBtn =
    document.getElementById("logoutBtn");

if (logoutBtn) {

    logoutBtn.addEventListener("click", () => {

        localStorage.removeItem("coalguard_user");

        currentUser = null;

        document.getElementById("appView")
            .classList.add("hidden");

        document.getElementById("loginView")
            .classList.remove("hidden");

        showToast("Signed out successfully");

    });

}


/* =========================================================
   LOAD MINE
========================================================= */

async function loadMine() {

    try {

        const data =
            await apiRequest("/api/mines");

        if (!data.mines || data.mines.length === 0) {
            return;
        }

       const mine =
    data.mines.find(
        m => m.id === currentMineId
    );

if (!mine) {
    console.error("Assigned mine not found");
    return;
}
currentMine = mine;

        currentMineId = mine.id;

        const mineName =
            document.getElementById("mineName");

        const mineLocation =
            document.getElementById("mineLocation");

        if (mineName) {
            mineName.textContent =
                mine.name;
        }

        if (mineLocation) {
            mineLocation.textContent =
                mine.location;
        }

    } catch (error) {

        console.error(
            "Unable to load mine",
            error
        );

    }

}


/* =========================================================
   DASHBOARD DATA
========================================================= */

async function loadDashboardData() {

    await loadEnvironmentalData();

    await loadRiskData();

}


/* =========================================================
   ENVIRONMENTAL DATA
========================================================= */

async function loadEnvironmentalData() {

    try {

        const data =
            await apiRequest(
                `/api/environmental/${currentMineId}`
            );

        const records =
            data.records || [];

        if (records.length === 0) {
            return;
        }

        updateEnvironmentCards(records);

        updateEnvironmentOverview(records);

        updateEnvironmentTable(records);

    } catch (error) {

        console.error(
            "Environmental data error:",
            error
        );

    }

}


/* =========================================================
   ENVIRONMENT CARDS
========================================================= */

function updateEnvironmentCards(records) {

    const latest = {};

    records.forEach(record => {

        if (!latest[record.parameter]) {

            latest[record.parameter] =
                record;

        }

    });


    /* Dust */

    if (latest["Dust"]) {

        const dust =
            latest["Dust"];

        document.getElementById(
            "dustStatus"
        ).textContent =
            dust.status;

        document.getElementById(
            "dustLatest"
        ).textContent =
            `${dust.value} ${dust.unit} · ${
                dust.status === "BREACH"
                    ? "above demo threshold"
                    : "within demo threshold"
            }`;

    }


    /* Water */

    if (latest["Water Quality"]) {

        const water =
            latest["Water Quality"];

        document.getElementById(
            "waterStatus"
        ).textContent =
            water.status;

        document.getElementById(
            "waterLatest"
        ).textContent =
            `${water.value} ${water.unit} · ${
                water.status === "BREACH"
                    ? "above demo threshold"
                    : "within demo threshold"
            }`;

    }


    /* Noise */

    if (latest["Noise"]) {

        const noise =
            latest["Noise"];

        document.getElementById(
            "noiseStatus"
        ).textContent =
            noise.status;

        document.getElementById(
            "noiseLatest"
        ).textContent =
            `${noise.value} ${noise.unit} · ${
                noise.status === "BREACH"
                    ? "above demo threshold"
                    : "within demo threshold"
            }`;

    }

}


/* =========================================================
   ENVIRONMENT OVERVIEW
========================================================= */

function updateEnvironmentOverview(records) {

    const container =
        document.getElementById("envOverview");

    if (!container) return;

    const latest = {};

    records.forEach(record => {

        if (!latest[record.parameter]) {
            latest[record.parameter] =
                record;
        }

    });

    container.innerHTML = "";

    Object.values(latest).forEach(record => {

        const statusClass =
            record.status === "BREACH"
                ? "danger"
                : "success";

        container.innerHTML += `

            <div class="env-row">

                <div class="env-symbol">
                    ${getParameterLetter(record.parameter)}
                </div>

                <div class="env-info">

                    <strong>
                        ${record.parameter}
                    </strong>

                    <small>
                        Latest reading
                    </small>

                </div>

                <div class="env-status">

                    <strong class="${statusClass}-text">
                        ${record.status}
                    </strong>

                    <small>
                        ${record.value} ${record.unit}
                    </small>

                </div>

            </div>

        `;

    });

}


/* =========================================================
   PARAMETER LETTER
========================================================= */

function getParameterLetter(parameter) {

    if (parameter === "Dust") {
        return "D";
    }

    if (parameter === "Water Quality") {
        return "W";
    }

    if (parameter === "Noise") {
        return "N";
    }

    return "E";
}


/* =========================================================
   ENVIRONMENT TABLE
========================================================= */

function updateEnvironmentTable(records) {

    const container =
        document.getElementById("envTable");

    if (!container) return;

    let html = `

        <table>

            <thead>

                <tr>
                    <th>PARAMETER</th>
                    <th>VALUE</th>
                    <th>THRESHOLD</th>
                    <th>STATUS</th>
                    <th>RECORDED</th>
                </tr>

            </thead>

            <tbody>

    `;

    records.forEach(record => {

        const statusClass =
            record.status === "BREACH"
                ? "breach"
                : "normal";

        const date =
            new Date(
                record.recorded_at
            ).toLocaleString();

        html += `

            <tr>

                <td>
                    <strong>
                        ${record.parameter}
                    </strong>
                </td>

                <td>
                    ${record.value}
                    ${record.unit}
                </td>

                <td>
                    ${record.threshold ?? "-"}
                </td>

                <td>
                    <span class="status-pill ${statusClass}">
                        ${record.status}
                    </span>
                </td>

                <td>
                    ${date}
                </td>

            </tr>

        `;

    });

    html += `

            </tbody>

        </table>

    `;

    container.innerHTML = html;

}


/* =========================================================
   REFRESH ENVIRONMENT
========================================================= */

const refreshEnv =
    document.getElementById("refreshEnv");

if (refreshEnv) {

    refreshEnv.addEventListener(
        "click",
        async () => {

            refreshEnv.textContent =
                "↻ Loading...";

            await loadEnvironmentalData();

            refreshEnv.textContent =
                "↻ Refresh data";

            showToast(
                "Environmental data refreshed"
            );

        }
    );

}


/* =========================================================
   RISK DATA
========================================================= */

async function loadRiskData() {

    try {

        const data =
            await apiRequest(
                `/api/risk/combined/${currentMineId}`
            );

        console.log(
            "Risk engine result:",
            data
        );

        /*
            IMPORTANT:
            Risk score is NOT displayed to the user.

            It is only used internally for:
            - GIS
            - Alerts
            - Prioritization
            - Corrective actions
        */

        updateRiskIndicators(data);

    } catch (error) {

        console.error(
            "Risk data error:",
            error
        );

    }

}


/* =========================================================
   RISK INDICATORS
========================================================= */

function updateRiskIndicators(data) {

    if (!data) return;

    /*
       We intentionally do NOT show:

       88
       100
       70

       Instead we show operational meaning.
    */

    const riskLevel =
        data.overall?.level || "HIGH";

    const heroTag =
        document.querySelector(
            ".hero-alert .tag"
        );

    if (heroTag) {

        heroTag.textContent =
            riskLevel === "HIGH"
                ? "ATTENTION REQUIRED"
                : "MONITOR";

    }

}


/* =========================================================
   NAVIGATION
========================================================= */

const navItems =
    document.querySelectorAll(
        ".nav-item[data-section]"
    );

navItems.forEach(item => {

    item.addEventListener(
        "click",
        () => {

            const section =
                item.dataset.section;

            openSection(section);

        }
    );

});


/* =========================================================
   SECTION JUMP BUTTONS
========================================================= */

const jumpButtons =
    document.querySelectorAll(
        "[data-section-jump]"
    );

jumpButtons.forEach(button => {

    button.addEventListener(
        "click",
        () => {

            const section =
                button.dataset.sectionJump;

            openSection(section);

        }
    );

});


/* =========================================================
   OPEN SECTION
========================================================= */

function openSection(sectionName) {

    const sections =
        document.querySelectorAll(
            ".section"
        );

    sections.forEach(section => {

        section.classList.remove(
            "active-section"
        );

    });


    const target =
        document.getElementById(
            sectionName
        );

    if (target) {

        target.classList.add(
            "active-section"
        );

    }


    navItems.forEach(item => {

        item.classList.remove("active");

        if (
            item.dataset.section ===
            sectionName
        ) {

            item.classList.add("active");

        }

    });


    updatePageTitle(sectionName);


    /* Load map when map section opens */

    if (sectionName === "map") {

        setTimeout(() => {

            if (fullMap) {
                fullMap.invalidateSize();
            }

        }, 100);

    }

}


/* =========================================================
   PAGE TITLE
========================================================= */

function updatePageTitle(section) {

    const title =
        document.getElementById(
            "sectionTitle"
        );

    const kicker =
        document.getElementById(
            "sectionKicker"
        );

    const titles = {

        overview: [
            "COMMAND CENTER",
            "Mine Overview"
        ],

        inspections: [
            "FIELD OPERATIONS",
            "Inspections & Violations"
        ],

        environment: [
            "ENVIRONMENTAL COMPLIANCE",
            "Environmental Monitoring"
        ],

        map: [
            "GEOSPATIAL OPERATIONS",
            "Risk & Compliance Map"
        ],

        actions: [
            "RESPONSE MANAGEMENT",
            "Corrective Actions"
        ],

        alerts: [
            "NOTIFICATIONS & ESCALATION",
            "Alerts"
        ]

    };


    if (titles[section]) {

        kicker.textContent =
            titles[section][0];

        title.textContent =
            titles[section][1];

    }

}


/* =========================================================
   INSPECTION MODAL
========================================================= */

const inspectionModal =
    document.getElementById(
        "inspectionModal"
    );

const newInspectionBtn =
    document.getElementById(
        "newInspectionBtn"
    );

const startInspectionBtn =
    document.getElementById(
        "startInspectionBtn"
    );


function openInspectionModal() {

    if (inspectionModal) {

        inspectionModal.classList.remove(
            "hidden"
        );

    }

}


function closeInspectionModal() {

    if (inspectionModal) {

        inspectionModal.classList.add(
            "hidden"
        );

    }

}


if (newInspectionBtn) {

    newInspectionBtn.addEventListener(
        "click",
        openInspectionModal
    );

}


if (startInspectionBtn) {

    startInspectionBtn.addEventListener(
        "click",
        openInspectionModal
    );

}


/* =========================================================
   CLOSE MODAL
========================================================= */

const modalClose =
    document.querySelector(
        ".modal-close"
    );

if (modalClose) {

    modalClose.addEventListener(
        "click",
        closeInspectionModal
    );

}


if (inspectionModal) {

    inspectionModal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                inspectionModal
            ) {

                closeInspectionModal();

            }

        }
    );

}


/* =========================================================
   CREATE INSPECTION
========================================================= */

const inspectionForm =
    document.getElementById(
        "inspectionForm"
    );

if (inspectionForm) {

    inspectionForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            if (!currentUser) {

                showToast(
                    "Please login first"
                );

                return;

            }


            const type =
                document.getElementById(
                    "inspectionType"
                ).value;

            const description =
                document.getElementById(
                    "inspectionDescription"
                ).value;

            const latitude =
                parseFloat(
                    document.getElementById(
                        "inspectionLat"
                    ).value
                );

            const longitude =
                parseFloat(
                    document.getElementById(
                        "inspectionLng"
                    ).value
                );


            try {

                const data =
                    await apiRequest(
                        "/api/inspections",
                        {

                            method: "POST",

                            body:
                                JSON.stringify({

                                    mine_id:
                                        currentMineId,

                                    inspector_id:
                                        currentUser.id,

                                    type:
                                        type,

                                    description:
                                        description,

                                    latitude:
                                        latitude,

                                    longitude:
                                        longitude

                                })

                        }
                    );


                showToast(
                    `Inspection #${data.inspection_id} created`
                );


                closeInspectionModal();

                inspectionForm.reset();


                /*
                   After creating an inspection,
                   refresh dashboard data.
                */

                await loadDashboardData();

            } catch (error) {

                console.error(error);

            }

        }
    );

}


/* =========================================================
   CORRECTIVE ACTION
========================================================= */

const createActionBtn =
    document.getElementById(
        "createActionBtn"
    );

if (createActionBtn) {

    createActionBtn.addEventListener(
        "click",
        async () => {

            try {

                /*
                   Current demo violation:
                   No Helmet = violation ID 4
                */

                const data =
                    await apiRequest(
                        "/api/actions",
                        {

                            method: "POST",

                            body:
                                JSON.stringify({

                                    violation_id: 4,

                                    assigned_to:
                                        currentUser?.id || 2,

                                    description:
                                        "Enforce helmet compliance in Section B and upload photographic proof.",

                                    deadline:
                                        "2026-09-11"

                                })

                        }
                    );


                showToast(
                    `Corrective Action #${data.action_id} created`
                );

            } catch (error) {

                console.error(error);

            }

        }
    );

}


/* =========================================================
   RESOLVE ACTION
========================================================= */

const resolveActionBtn =
    document.getElementById(
        "resolveActionBtn"
    );

if (resolveActionBtn) {

    resolveActionBtn.addEventListener(
        "click",
        async () => {

            /*
               Demo action ID.
               We can make this dynamic later.
            */

            const actionId = 4;

            try {

                const data =
                    await apiRequest(
                        `/api/actions/${actionId}`,
                        {

                            method: "PUT",

                            body:
                                JSON.stringify({

                                    status:
                                        "RESOLVED",

                                    proof_url:
                                        "demo/helmet-compliance-proof.jpg",

                                    verified_by:
                                        currentUser?.id || 2

                                })

                        }
                    );


                showToast(
                    `Action #${data.action_id} resolved`
                );


                resolveActionBtn.textContent =
                    "✓ Resolved";

                resolveActionBtn.disabled =
                    true;

            } catch (error) {

                console.error(error);

            }

        }
    );

}


/* =========================================================
   MARK ALL ALERTS READ
========================================================= */

const markReadBtn =
    document.getElementById(
        "markReadBtn"
    );

if (markReadBtn) {

    markReadBtn.addEventListener(
        "click",
        () => {

            const unreadAlerts =
                document.querySelectorAll(
                    ".big-alert.unread"
                );

            unreadAlerts.forEach(alert => {

                alert.classList.remove(
                    "unread"
                );

            });


            markReadBtn.textContent =
                "✓ All read";

            showToast(
                "All alerts marked as read"
            );

        }
    );

}


/* =========================================================
   NOTIFICATION BUTTON
========================================================= */

const notificationBtn =
    document.getElementById(
        "notificationBtn"
    );

if (notificationBtn) {

    notificationBtn.addEventListener(
        "click",
        () => {

            openSection("alerts");

        }
    );

}


/* =========================================================
   GIS MAPS
========================================================= */

function initializeMaps() {

    if (
        typeof L === "undefined"
    ) {

        console.error(
            "Leaflet library not loaded"
        );

        return;

    }


    initializeMiniMap();

    initializeFullMap();

}


/* =========================================================
   MINI MAP
========================================================= */

function initializeMiniMap() {

    const mapElement =
        document.getElementById(
            "miniMap"
        );

    if (!mapElement) return;

    if (miniMap) return;


    miniMap =
        L.map("miniMap", {
            zoomControl: false
        }).setView(
            [21.2787, 81.8661],
            13
        );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {

            attribution:
                "&copy; OpenStreetMap contributors",

            maxZoom: 19

        }
    ).addTo(miniMap);


    addMineMarkers(miniMap);


    setTimeout(() => {

        miniMap.invalidateSize();

    }, 300);

}


/* =========================================================
   FULL MAP
========================================================= */

function initializeFullMap() {

    const mapElement =
        document.getElementById(
            "fullMap"
        );

    if (!mapElement) return;

    if (fullMap) return;


    fullMap =
        L.map("fullMap")
            .setView(
                [21.2787, 81.8661],
                13
            );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {

            attribution:
                "&copy; OpenStreetMap contributors",

            maxZoom: 19

        }
    ).addTo(fullMap);


    addMineMarkers(fullMap);


    setTimeout(() => {

        fullMap.invalidateSize();

    }, 300);

}


/* =========================================================
   ADD GIS MARKERS
========================================================= */

function addMineMarkers(map) {

    // Logged-in user's assigned mine
    const mineLat = Number(currentMine?.latitude) || 21.2787;
const mineLng = Number(currentMine?.longitude)|| 81.8661;
const mineName = currentMine?.name || "Mine";
const mineLocation = currentMine?.location || "Unknown";


    // =========================
    // MINE
    // =========================

    const mineMarker =
        L.marker(
            [mineLat, mineLng]
        ).addTo(map);

    mineMarker.bindPopup(`

        <strong>${mineName}</strong><br>

        ${mineLocation}<br>

        <b>Status:</b> Active

    `);


    // =========================
    // HIGH - NO HELMET
    // RED
    // =========================

    const violationMarker =
        L.circleMarker(
            [mineLat, mineLng],
            {
                radius: 11,

                fillColor: "#dc2626",

                color: "#b91c1c",

                fillOpacity: 0.8,

                weight: 3
            }
        ).addTo(map);

    violationMarker.bindPopup(`

        <strong>Section B</strong><br>

        No Helmet / PPE<br>

        <b>Priority:</b> HIGH<br>

        <b>Status:</b> OPEN

    `);


    // =========================
    // HIGH - DUST
    // RED
    // =========================

    const dustMarker =
        L.circleMarker(
            [mineLat + 0.0023, mineLng + 0.0029],
            {
                radius: 9,

                fillColor: "#dc2626",

                color: "#b91c1c",

                fillOpacity: 0.7,

                weight: 2
            }
        ).addTo(map);

    dustMarker.bindPopup(`

        <strong>Dust Monitoring Point</strong><br>

        Environmental breach<br>

        <b>Priority:</b> HIGH<br>

        <b>Status:</b> BREACH

    `);


    // =========================
    // MEDIUM - WATER
    // ORANGE
    // =========================

    const waterMarker =
        L.circleMarker(
            [mineLat - 0.0022, mineLng - 0.0031],
            {
                radius: 8,

                fillColor: "#f59e0b",

                color: "#d97706",

                fillOpacity: 0.7,

                weight: 2
            }
        ).addTo(map);

    waterMarker.bindPopup(`

        <strong>Water Quality Point</strong><br>

        Environmental breach<br>

        <b>Priority:</b> MEDIUM<br>

        <b>Status:</b> BREACH

    `);

}

/* =========================================================
   MAP FILTER BUTTONS
========================================================= */

const filterButtons =
    document.querySelectorAll(
        ".map-filter .filter"
    );

filterButtons.forEach(button => {

    button.addEventListener(
        "click",
        () => {

            filterButtons.forEach(btn => {

                btn.classList.remove(
                    "active"
                );

            });

            button.classList.add(
                "active"
            );

            showToast(
                `${button.textContent} map filter selected`
            );

        }
    );

});


/* =========================================================
   NEW ACTION BUTTON
========================================================= */

const newActionBtn =
    document.getElementById(
        "newActionBtn"
    );

if (newActionBtn) {

    newActionBtn.addEventListener(
        "click",
        () => {

            if (createActionBtn) {

                createActionBtn.click();

            }

            openSection("actions");

        }
    );

}


/* =========================================================
   INITIAL STATE
========================================================= */

function initializeApp() {

    /*
       Keep application hidden
       until login is successful.
    */

    const appView =
        document.getElementById(
            "appView"
        );

    const loginView =
        document.getElementById(
            "loginView"
        );

    if (
        !localStorage.getItem(
            "coalguard_user"
        )
    ) {

        appView.classList.add(
            "hidden"
        );

        loginView.classList.remove(
            "hidden"
        );

    }

}


initializeApp();


/* =========================================================
   CONSOLE MESSAGE
========================================================= */

console.log(
    "CoalGuard AI frontend loaded successfully."
);
