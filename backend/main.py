from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db_connection

app = FastAPI(title="CoalGuard AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Login Request Model
# -------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


# -------------------------
# Home API
# -------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "CoalGuard AI"}


# -------------------------
# Login API
# -------------------------
@app.post("/api/auth/login")
def login(data: LoginRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, role, mine_id
        FROM users
        WHERE email = %s AND password_hash = %s
    """, (data.email, data.password))

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


# -------------------------
# Get Mines API
# -------------------------
@app.get("/api/mines")
def get_mines():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, location, status
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

from pydantic import BaseModel


class InspectionRequest(BaseModel):
    mine_id: int
    inspector_id: int
    type: str
    description: str = ""
    latitude: float | None = None
    longitude: float | None = None


@app.post("/api/inspections")
def create_inspection(data: InspectionRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspections
        (mine_id, inspector_id, type, description, latitude, longitude)
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
# -------------------------
# Violation Request Model
# -------------------------
class ViolationRequest(BaseModel):
    inspection_id: int
    mine_id: int
    type: str
    severity: str
    description: str = ""
    photo_url: str = ""
    latitude: float | None = None
    longitude: float | None = None


# -------------------------
# Create Violation API
# -------------------------
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

# -------------------------
# Risk Score API
# -------------------------
@app.get("/api/risk/{mine_id}")
def calculate_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all violations for this mine
    cursor.execute("""
        SELECT severity, type, status
        FROM violations
        WHERE mine_id = %s
    """, (mine_id,))

    violations = cursor.fetchall()

    # Calculate risk score
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

        # Extra risk for an unresolved violation
        if status == "OPEN":
            score += 10
            reasons.append(
                f"Open violation: {violation_type}"
            )

    # Maximum score = 100
    score = min(score, 100)

    # Determine risk level
    if score <= 30:
        level = "LOW"
    elif score <= 60:
        level = "MEDIUM"
    else:
        level = "HIGH"

    reason_text = "; ".join(reasons)

    # Save risk score
    cursor.execute("""
        INSERT INTO risk_scores
        (mine_id, score, level, reasons)
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
# -------------------------
# Manager Alert API
# -------------------------
class AlertRequest(BaseModel):
    user_id: int
    message: str
    type: str = "HIGH_RISK"


@app.post("/api/alerts")
def create_alert(data: AlertRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notifications
        (user_id, type, message)
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
# -------------------------
# Environmental Record Request
# -------------------------
class EnvironmentalRequest(BaseModel):
    mine_id: int
    parameter: str
    value: float
    unit: str
    threshold: float | None = None
    status: str = "NORMAL"
    description: str = ""


# -------------------------
# Create Environmental Record
# -------------------------
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


# -------------------------
# Get Environmental Records
# -------------------------
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
                "threshold": float(record[4]) if record[4] is not None else None,
                "status": record[5],
                "description": record[6],
                "recorded_at": record[7]
            }
            for record in records
        ]
    }
# -------------------------
# Environmental Risk API
# -------------------------
@app.get("/api/environmental-risk/{mine_id}")
def environmental_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT parameter, status
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

            parameter_breaches[parameter] = \
                parameter_breaches.get(parameter, 0) + 1

    # Risk based on number of breaches
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

    # Extra risk for repeated same parameter
    for parameter, count in parameter_breaches.items():

        if count >= 2:

            score += 10

            reasons.append(
                f"Repeated {parameter} issue"
            )

    score = min(score, 100)

    # Risk level
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
# -------------------------
# Combined Safety + Environmental Risk API
# -------------------------
@app.get("/api/risk/combined/{mine_id}")
def combined_risk(mine_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # SAFETY RISK
    # =========================

    cursor.execute("""
        SELECT severity, type, status
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

        if status == "OPEN":
            safety_score += 10

            safety_reasons.append(
                f"Open violation: {violation_type}"
            )

    safety_score = min(safety_score, 100)

    # Safety level
    if safety_score <= 30:
        safety_level = "LOW"

    elif safety_score <= 60:
        safety_level = "MEDIUM"

    else:
        safety_level = "HIGH"


    # =========================
    # ENVIRONMENTAL RISK
    # =========================

    cursor.execute("""
        SELECT parameter, status
        FROM environmental_records
        WHERE mine_id = %s
    """, (mine_id,))

    environmental_records = cursor.fetchall()

    environmental_score = 0
    environmental_reasons = []

    breach_count = 0
    parameter_breaches = {}

    for parameter, status in environmental_records:

        if status == "BREACH":

            breach_count += 1

            parameter_breaches[parameter] = \
                parameter_breaches.get(parameter, 0) + 1


    # Environmental breach risk
    if breach_count >= 4:

        environmental_score += 60

        environmental_reasons.append(
            "Multiple environmental compliance breaches"
        )

    elif breach_count >= 2:

        environmental_score += 40

        environmental_reasons.append(
            "Repeated environmental breaches"
        )

    elif breach_count == 1:

        environmental_score += 25

        environmental_reasons.append(
            "Environmental compliance breach"
        )


    # Repeated environmental parameter
    for parameter, count in parameter_breaches.items():

        if count >= 2:

            environmental_score += 10

            environmental_reasons.append(
                f"Repeated {parameter} issue"
            )

    environmental_score = min(environmental_score, 100)


    # Environmental level
    if environmental_score <= 30:
        environmental_level = "LOW"

    elif environmental_score <= 60:
        environmental_level = "MEDIUM"

    else:
        environmental_level = "HIGH"


    # =========================
    # OVERALL RISK
    # =========================

    overall_score = round(
        (safety_score * 0.60) +
        (environmental_score * 0.40)
    )

    if overall_score <= 30:
        overall_level = "LOW"

    elif overall_score <= 60:
        overall_level = "MEDIUM"

    else:
        overall_level = "HIGH"


    cursor.close()
    conn.close()


    # =========================
    # FINAL RESPONSE
    # =========================

    return {

        "mine_id": mine_id,

        "safety": {
            "score": safety_score,
            "level": safety_level,
            "reasons": safety_reasons
        },

        "environment": {
            "score": environmental_score,
            "level": environmental_level,
            "breach_count": breach_count,
            "reasons": environmental_reasons
        },

        "overall": {
            "score": overall_score,
            "level": overall_level
        }
    }

# =========================================================
# Serve the responsive frontend from the same backend URL
# =========================================================
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
