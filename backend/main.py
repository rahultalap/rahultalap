from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db_connection


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="CoalGuard AI API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # MINES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mines (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            status VARCHAR(50) DEFAULT 'ACTIVE'
        );
    """)

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'INSPECTOR',
            mine_id INTEGER REFERENCES mines(id)
        );
    """)

    # -----------------------------------------------------
    # INSPECTIONS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id SERIAL PRIMARY KEY,
            mine_id INTEGER REFERENCES mines(id),
            inspector_id INTEGER REFERENCES users(id),
            type VARCHAR(100),
            description TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------
    # VIOLATIONS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id SERIAL PRIMARY KEY,
            inspection_id INTEGER REFERENCES inspections(id),
            mine_id INTEGER REFERENCES mines(id),
            type VARCHAR(100),
            severity VARCHAR(50),
            description TEXT,
            photo_url TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            status VARCHAR(50) DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------
    # RISK SCORES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id SERIAL PRIMARY KEY,
            mine_id INTEGER REFERENCES mines(id),
            score NUMERIC,
            level VARCHAR(50),
            reasons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------
    # NOTIFICATIONS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            type VARCHAR(100),
            message TEXT,
            read_status BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------
    # ENVIRONMENTAL RECORDS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS environmental_records (
            id SERIAL PRIMARY KEY,
            mine_id INTEGER REFERENCES mines(id),
            parameter VARCHAR(100),
            value DOUBLE PRECISION,
            unit VARCHAR(50),
            threshold DOUBLE PRECISION,
            status VARCHAR(50) DEFAULT 'NORMAL',
            description TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------
    # DEMO MINE
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO mines
            (name, location, status)
        SELECT
            'Dharmaband Central Coal Mine',
            'Jharia Coalfield, Dhanbad, Jharkhand',
            'ACTIVE'
        WHERE NOT EXISTS (
            SELECT 1
            FROM mines
            WHERE name = 'Dharmaband Central Coal Mine'
        );
    """)

# -----------------------------------------------------
    # DEMO USERS
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, mine_id)
        VALUES (
            'Admin User',
            'admin@coalguard.com',
            'admin123',
            'ADMIN',
            (SELECT id FROM mines
             WHERE name = 'Dharmaband Central Coal Mine'
             LIMIT 1)
        )
        ON CONFLICT (email)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            mine_id = EXCLUDED.mine_id;
    """)

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, mine_id)
        VALUES (
            'Mine Manager',
            'manager@coalguard.com',
            'manager123',
            'MANAGER',
            (SELECT id FROM mines
             WHERE name = 'Dharmaband Central Coal Mine'
             LIMIT 1)
        )
        ON CONFLICT (email)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            mine_id = EXCLUDED.mine_id;
    """)

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, mine_id)
        VALUES (
            'Rahul Inspector',
            'inspector@coalguard.com',
            'inspector123',
            'INSPECTOR',
            (SELECT id FROM mines
             WHERE name = 'Dharmaband Central Coal Mine'
             LIMIT 1)
        )
        ON CONFLICT (email)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            mine_id = EXCLUDED.mine_id;
    """)

    conn.commit()
    cursor.close()
    conn.close()

# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    try:
        init_database()
        print("Database initialized successfully.")

    except Exception as e:
        print("Database initialization failed:", e)


# =========================================================
# LOGIN REQUEST MODEL
# =========================================================

class LoginRequest(BaseModel):
    email: str
    password: str


# =========================================================
# HEALTH API
# =========================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "CoalGuard AI"
    }


# =========================================================
# LOGIN API
# =========================================================

@app.post("/api/auth/login")
def login(data: LoginRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            role,
            mine_id
        FROM users
        WHERE email = %s
        AND password_hash = %s
    """, (
        data.email,
        data.password
    ))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user": {
            "id": user[0],
            "name": user[1],
            "role": user[2],
            "mine_id": user[3]
        }
    }


# =========================================================
# GET MINES
# =========================================================

@app.get("/api/mines")
def get_mines():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            location,
            status
        FROM mines
        ORDER BY id
    """)

    mines = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "mines": [
            {
                "id": mine[0],
                "name": mine[1],
                "location": mine[2],
                "status": mine[3]
            }
            for mine in mines
        ]
    }


# =========================================================
# INSPECTION REQUEST MODEL
# =========================================================

class InspectionRequest(BaseModel):

    mine_id: int
    inspector_id: int
    type: str
    description: str = ""
    latitude: float | None = None
    longitude: float | None = None


# =========================================================
# CREATE INSPECTION
# =========================================================

@app.post("/api/inspections")
def create_inspection(data: InspectionRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspections
        (
            mine_id,
            inspector_id,
            type,
            description,
            latitude,
            longitude
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data.mine_id,
        data.inspector_id,
        data.type,
        data.description,
        data.latitude,
        data.longitude
    ))

    inspection_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Inspection created successfully",
        "inspection_id": inspection_id
    }


# =========================================================
# VIOLATION REQUEST MODEL
# =========================================================

class ViolationRequest(BaseModel):

    inspection_id: int
    mine_id: int
    type: str
    severity: str
    description: str = ""
    photo_url: str = ""
    latitude: float | None = None
    longitude: float | None = None


# =========================================================
# CREATE VIOLATION
# =========================================================

@app.post("/api/violations")
def create_violation(data: ViolationRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO violations
        (
            inspection_id,
            mine_id,
            type,
            severity,
            description,
            photo_url,
            latitude,
            longitude
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data.inspection_id,
        data.mine_id,
        data.type,
        data.severity,
        data.description,
        data.photo_url,
        data.latitude,
        data.longitude
    ))

    violation_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Violation created successfully",
        "violation_id": violation_id,
        "status": "OPEN"
    }


# =========================================================
# RISK SCORE API
# =========================================================

@app.get("/api/risk/{mine_id}")
def calculate_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            severity,
            type,
            status
        FROM violations
        WHERE mine_id = %s
    """, (mine_id,))

    violations = cursor.fetchall()

    score = 0
    reasons = []

    for violation in violations:

        severity = violation[0]
        violation_type = violation[1]
        status = violation[2]

        if severity == "HIGH":

            score += 40

            reasons.append(
                f"High severity violation: {violation_type}"
            )

        elif severity == "MEDIUM":

            score += 20

        elif severity == "LOW":

            score += 10

        if status == "OPEN":

            score += 10

            reasons.append(
                f"Open violation: {violation_type}"
            )

    score = min(score, 100)

    if score <= 30:

        level = "LOW"

    elif score <= 60:

        level = "MEDIUM"

    else:

        level = "HIGH"

    reason_text = "; ".join(reasons)

    cursor.execute("""
        INSERT INTO risk_scores
        (
            mine_id,
            score,
            level,
            reasons
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        mine_id,
        score,
        level,
        reason_text
    ))

    risk_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "risk_id": risk_id,
        "mine_id": mine_id,
        "score": score,
        "level": level,
        "reasons": reasons
    }


# =========================================================
# ALERT REQUEST
# =========================================================

class AlertRequest(BaseModel):

    user_id: int
    message: str
    type: str = "HIGH_RISK"


# =========================================================
# CREATE ALERT
# =========================================================

@app.post("/api/alerts")
def create_alert(data: AlertRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notifications
        (
            user_id,
            type,
            message
        )
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        data.user_id,
        data.type,
        data.message
    ))

    alert_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Alert created successfully",
        "alert_id": alert_id,
        "read_status": False
    }


# =========================================================
# ENVIRONMENTAL REQUEST
# =========================================================

class EnvironmentalRequest(BaseModel):

    mine_id: int
    parameter: str
    value: float
    unit: str
    threshold: float | None = None
    status: str = "NORMAL"
    description: str = ""


# =========================================================
# CREATE ENVIRONMENTAL RECORD
# =========================================================

@app.post("/api/environmental")
def create_environmental_record(data: EnvironmentalRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO environmental_records
        (
            mine_id,
            parameter,
            value,
            unit,
            threshold,
            status,
            description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data.mine_id,
        data.parameter,
        data.value,
        data.unit,
        data.threshold,
        data.status,
        data.description
    ))

    record_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Environmental record created successfully",
        "record_id": record_id,
        "status": data.status
    }


# =========================================================
# GET ENVIRONMENTAL RECORDS
# =========================================================

@app.get("/api/environmental/{mine_id}")
def get_environmental_records(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            parameter,
            value,
            unit,
            threshold,
            status,
            description,
            recorded_at
        FROM environmental_records
        WHERE mine_id = %s
        ORDER BY recorded_at DESC
    """, (mine_id,))

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "mine_id": mine_id,
        "records": [
            {
                "id": record[0],
                "parameter": record[1],
                "value": float(record[2]),
                "unit": record[3],
                "threshold": (
                    float(record[4])
                    if record[4] is not None
                    else None
                ),
                "status": record[5],
                "description": record[6],
                "recorded_at": record[7]
            }
            for record in records
        ]
    }


# =========================================================
# ENVIRONMENTAL RISK
# =========================================================

@app.get("/api/environmental-risk/{mine_id}")
def environmental_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            parameter,
            status
        FROM environmental_records
        WHERE mine_id = %s
    """, (mine_id,))

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    if not records:

        return {
            "mine_id": mine_id,
            "environmental_score": 0,
            "level": "LOW",
            "breach_count": 0,
            "reasons": []
        }

    score = 0
    reasons = []

    breach_count = 0
    parameter_breaches = {}

    for parameter, status in records:

        if status == "BREACH":

            breach_count += 1

            parameter_breaches[parameter] = (
                parameter_breaches.get(parameter, 0) + 1
            )

    if breach_count >= 4:

        score += 60

        reasons.append(
            "Multiple environmental compliance breaches"
        )

    elif breach_count >= 2:

        score += 40

        reasons.append(
            "Repeated environmental breaches"
        )

    elif breach_count == 1:

        score += 25

        reasons.append(
            "Environmental compliance breach"
        )

    for parameter, count in parameter_breaches.items():

        if count >= 2:

            score += 10

            reasons.append(
                f"Repeated {parameter} issue"
            )

    score = min(score, 100)

    if score <= 30:

        level = "LOW"

    elif score <= 60:

        level = "MEDIUM"

    else:

        level = "HIGH"

    return {
        "mine_id": mine_id,
        "environmental_score": score,
        "level": level,
        "breach_count": breach_count,
        "reasons": reasons
    }


# =========================================================
# COMBINED RISK
# =========================================================

@app.get("/api/risk/combined/{mine_id}")
def combined_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================================
    # SAFETY RISK
    # =====================================================

    cursor.execute("""
        SELECT
            severity,
            type,
            status
        FROM violations
        WHERE mine_id = %s
    """, (mine_id,))

    violations = cursor.fetchall()

    safety_score = 0
    safety_reasons = []

    for violation in violations:

        severity = violation[0]
        violation_type = violation[1]
        status = violation[2]

        if severity == "HIGH":

            safety_score += 40

            safety_reasons.append(
                f"High severity violation: {violation_type}"
            )

        elif severity == "MEDIUM":

            safety_score += 20

        elif severity == "LOW":

            safety_score += 10

        if status in ("OPEN", "IN_PROGRESS"):

            safety_score += 10

            safety_reasons.append(
                f"Unresolved violation: {violation_type}"
            )

    safety_score = min(safety_score, 100)

    if safety_score < 35:

        safety_level = "LOW"

    elif safety_score < 70:

        safety_level = "MEDIUM"

    else:

        safety_level = "HIGH"


    # =====================================================
    # ENVIRONMENTAL RISK
    # =====================================================

    cursor.execute("""
        SELECT
            parameter,
            status
        FROM environmental_records
        WHERE mine_id = %s
    """, (mine_id,))

    environmental_records = cursor.fetchall()

    environmental_score = 0
    environmental_reasons = []

    breach_count = 0
    warning_count = 0

    for parameter, status in environmental_records:

        if status == "CRITICAL":

            environmental_score += 30

            environmental_reasons.append(
                f"Critical environmental reading: {parameter}"
            )

        elif status == "WARNING":

            environmental_score += 15

            environmental_reasons.append(
                f"Warning environmental reading: {parameter}"
            )

    environmental_score = min(environmental_score, 100)

    if environmental_score < 35:

        environmental_level = "LOW"

    elif environmental_score < 70:

        environmental_level = "MEDIUM"

    else:

        environmental_level = "HIGH"


    # =====================================================
    # COMPLIANCE RISK
    # =====================================================

    compliance_score = 0

    compliance_reasons = []

    # Open / in-progress violations
    for violation in violations:

        status = violation[2]

        if status in ("OPEN", "IN_PROGRESS"):

            compliance_score += 10

    # Incomplete inspections
    cursor.execute("""
        SELECT COUNT(*)
        FROM inspections i
        WHERE i.mine_id = %s
        AND NOT EXISTS (
            SELECT 1
            FROM violations v
            WHERE v.inspection_id = i.id
        )
    """, (mine_id,))

    incomplete_inspections = cursor.fetchone()[0]

    compliance_score += incomplete_inspections * 20

    compliance_score = min(compliance_score, 100)

    if compliance_score < 35:

        compliance_level = "LOW"

    elif compliance_score < 70:

        compliance_level = "MEDIUM"

    else:

        compliance_level = "HIGH"


    # =====================================================
    # OVERALL RISK
    # =====================================================

    overall_score = round(
        (environmental_score * 0.40)
        +
        (safety_score * 0.40)
        +
        (compliance_score * 0.20)
    )

    overall_score = min(overall_score, 100)

    if overall_score < 35:

        overall_level = "LOW"

    elif overall_score < 70:

        overall_level = "MEDIUM"

    else:

        overall_level = "HIGH"


    cursor.close()
    conn.close()


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "mine_id": mine_id,

        "environment": {
            "score": environmental_score,
            "level": environmental_level,
            "breach_count": breach_count,
            "reasons": environmental_reasons
        },

        "safety": {
            "score": safety_score,
            "level": safety_level,
            "reasons": safety_reasons
        },

        "compliance": {
            "score": compliance_score,
            "level": compliance_level,
            "incomplete_inspections": incomplete_inspections,
            "reasons": compliance_reasons
        },

        "overall": {
            "score": overall_score,
            "level": overall_level
        }
    }


# =========================================================
# SERVE FRONTEND
# =========================================================

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)
