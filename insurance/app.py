
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from typing import List, Dict
import os
import csv
import io
import re

app = Flask(__name__)

# Data Models
class Policyholder:
    """Represents an insurance policyholder."""
    def __init__(self, name: str, age: int, policy_type: str, sum_insured: float):
        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.policy_type = policy_type
        self.sum_insured = sum_insured

class Claim:
    """Represents an insurance claim."""
    def __init__(self, policyholder_id: str, claim_amount: float, reason: str):
        self.id = str(uuid.uuid4())
        self.policyholder_id = policyholder_id
        self.claim_amount = claim_amount
        self.reason = reason
        self.status = "Pending"
        self.date = datetime.now()

# In-memory storage
class InsuranceManager:
    """Manages policyholders and claims with persistence and risk analysis."""
    def __init__(self):
        self.policyholders: Dict[str, Policyholder] = {}
        self.claims: Dict[str, Claim] = {}
        self.load_data()
        self.load_csv_data()

    def load_data(self):
        """Load policyholders and claims from JSON file."""
        try:
            if os.path.exists("data.json"):
                with open("data.json", "r") as f:
                    data = json.load(f)
                    for ph_data in data.get("policyholders", []):
                        ph = Policyholder(ph_data["name"], ph_data["age"], ph_data["policy_type"], ph_data["sum_insured"])
                        ph.id = ph_data["id"]
                        self.policyholders[ph.id] = ph
                    for claim_data in data.get("claims", []):
                        claim = Claim(claim_data["policyholder_id"], claim_data["claim_amount"], claim_data["reason"])
                        claim.id = claim_data["id"]
                        claim.status = claim_data["status"]
                        claim.date = datetime.fromisoformat(claim_data["date"])
                        self.claims[claim.id] = claim
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading JSON data: {e}")

    def load_csv_data(self):
        """Load claims from Insurance_auto_data.csv."""
        try:
            with open("Insurance_auto_data.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customer_id = row["CUSTOMER_ID"]
                    # Create policyholder if not exists
                    if customer_id not in self.policyholders:
                        self.policyholders[customer_id] = Policyholder(
                            name=f"Customer {customer_id}",
                            age=30,  # Default age
                            policy_type="Vehicle",  # Default policy type
                            sum_insured=float(row["CLAIM_AMOUNT"]) * 2 if row["CLAIM_AMOUNT"] else 100000.0
                        )
                    # Add claim
                    if row["CLAIM_AMOUNT"]:
                        claim = Claim(
                            policyholder_id=customer_id,
                            claim_amount=float(row["CLAIM_AMOUNT"]),
                            reason=row["REJECTION_REMARKS"] or "Vehicle damage"
                        )
                        claim.id = row["CLAIM_ID"]
                        claim.date = datetime.strptime(row["CLAIM_DATE"], "%Y-%m-%d")
                        claim.status = "Rejected" if row["REJECTION_REMARKS"] else "Approved" if row["PAID_AMOUNT"] else "Pending"
                        self.claims[claim.id] = claim
            self.save_data()
        except (IOError, ValueError) as e:
            print(f"Error loading CSV data: {e}")

    def save_data(self):
        """Save policyholders and claims to JSON file."""
        try:
            data = {
                "policyholders": [
                    {"id": ph.id, "name": ph.name, "age": ph.age, "policy_type": ph.policy_type, "sum_insured": ph.sum_insured}
                    for ph in self.policyholders.values()
                ],
                "claims": [
                    {"id": c.id, "policyholder_id": c.policyholder_id, "claim_amount": c.claim_amount, "reason": c.reason, 
                     "status": c.status, "date": c.date.isoformat()}
                    for c in self.claims.values()
                ]
            }
            with open("data.json", "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving data: {e}")

    def add_policyholder(self, name: str, age: int, policy_type: str, sum_insured: float) -> str:
        """Add a new policyholder with validation."""
        if not name or not re.match(r"^[A-Za-z\s]+$", name):
            raise ValueError("Invalid name (letters and spaces only)")
        if age < 18 or age > 100:
            raise ValueError("Age must be between 18 and 100")
        if policy_type not in ["Health", "Vehicle", "Life"]:
            raise ValueError("Invalid policy type")
        if sum_insured <= 0 or sum_insured > 10000000:
            raise ValueError("Sum insured must be between 1 and 10,000,000")
        policyholder = Policyholder(name, age, policy_type, sum_insured)
        self.policyholders[policyholder.id] = policyholder
        self.save_data()
        return policyholder.id

    def add_claim(self, policyholder_id: str, claim_amount: float, reason: str) -> str:
        """Add a new claim with validation."""
        if policyholder_id not in self.policyholders:
            raise ValueError("Policyholder not found")
        if claim_amount <= 0 or claim_amount > self.policyholders[policyholder_id].sum_insured:
            raise ValueError("Invalid claim amount (must be positive and not exceed sum insured)")
        if not reason or len(reason) > 500:
            raise ValueError("Reason must be non-empty and less than 500 characters")
        claim = Claim(policyholder_id, claim_amount, reason)
        self.claims[claim.id] = claim
        self.save_data()
        return claim.id

    def update_claim_status(self, claim_id: str, status: str):
        """Update claim status with validation."""
        if claim_id not in self.claims:
            raise ValueError("Claim not found")
        if status not in ["Pending", "Approved", "Rejected"]:
            raise ValueError("Invalid status")
        if self.claims[claim_id].status == "Approved" and status == "Pending":
            raise ValueError("Cannot revert Approved to Pending")
        self.claims[claim_id].status = status
        self.save_data()

    def get_claim_frequency(self, policyholder_id: str) -> int:
        """Calculate number of claims for a policyholder."""
        if policyholder_id not in self.policyholders:
            raise ValueError("Policyholder not found")
        return len([c for c in self.claims.values() if c.policyholder_id == policyholder_id])

    def get_high_risk_policyholders(self) -> List[Dict]:
        """Identify high-risk policyholders based on claim frequency and ratio."""
        one_year_ago = datetime.now() - timedelta(days=365)
        high_risk = []
        for ph in self.policyholders.values():
            claims = [c for c in self.claims.values() if c.policyholder_id == ph.id]
            recent_claims = [c for c in claims if c.date >= one_year_ago]
            rejected_claims = len([c for c in claims if c.status == "Rejected"])
            total_claim_amount = sum(c.claim_amount for c in claims if c.status == "Approved")
            claim_ratio = total_claim_amount / ph.sum_insured if ph.sum_insured > 0 else 0
            if len(recent_claims) > 3 or claim_ratio > 0.8 or rejected_claims > 2:
                high_risk.append({
                    "id": ph.id, "name": ph.name, "claim_count": len(recent_claims), 
                    "claim_ratio": claim_ratio, "rejected_count": rejected_claims
                })
        return high_risk

    def get_claims_by_policy_type(self) -> Dict[str, int]:
        """Count claims by policy type."""
        result = {"Health": 0, "Vehicle": 0, "Life": 0}
        for claim in self.claims.values():
            ph = self.policyholders.get(claim.policyholder_id)
            if ph:
                result[ph.policy_type] += 1
        return result

    def get_monthly_claims(self) -> Dict[str, int]:
        """Count claims by month."""
        result = {}
        for claim in self.claims.values():
            month = claim.date.strftime("%Y-%m")
            result[month] = result.get(month, 0) + 1
        return result

    def get_avg_claim_amount_by_policy_type(self) -> Dict[str, float]:
        """Calculate average claim amount by policy type."""
        sums = {"Health": 0, "Vehicle": 0, "Life": 0}
        counts = {"Health": 0, "Vehicle": 0, "Life": 0}
        for claim in self.claims.values():
            ph = self.policyholders.get(claim.policyholder_id)
            if ph and claim.status == "Approved":
                sums[ph.policy_type] += claim.claim_amount
                counts[ph.policy_type] += 1
        return {k: sums[k] / counts[k] if counts[k] > 0 else 0 for k in sums}

    def get_highest_claim(self) -> Dict:
        """Get the highest approved claim."""
        approved_claims = [c for c in self.claims.values() if c.status == "Approved"]
        if not approved_claims:
            return {}
        max_claim = max(approved_claims, key=lambda c: c.claim_amount)
        ph = self.policyholders.get(max_claim.policyholder_id)
        return {
            "claim_id": max_claim.id, "policyholder_name": ph.name if ph else "Unknown",
            "amount": max_claim.claim_amount, "reason": max_claim.reason
        }

    def get_pending_claims(self) -> List[Dict]:
        """List all pending claims."""
        return [
            {"claim_id": c.id, "policyholder_name": self.policyholders[c.policyholder_id].name, 
             "amount": c.claim_amount, "reason": c.reason}
            for c in self.claims.values() if c.status == "Pending"
        ]

    def get_policyholder(self, policyholder_id: str) -> Dict:
        """Retrieve policyholder details."""
        if policyholder_id not in self.policyholders:
            raise ValueError("Policyholder not found")
        ph = self.policyholders[policyholder_id]
        return {
            "id": ph.id, "name": ph.name, "age": ph.age, 
            "policy_type": ph.policy_type, "sum_insured": ph.sum_insured
        }

    def get_claim(self, claim_id: str) -> Dict:
        """Retrieve claim details."""
        if claim_id not in self.claims:
            raise ValueError("Claim not found")
        c = self.claims[claim_id]
        ph = self.policyholders.get(c.policyholder_id)
        return {
            "id": c.id, "policyholder_name": ph.name if ph else "Unknown",
            "claim_amount": c.claim_amount, "reason": c.reason,
            "status": c.status, "date": c.date.isoformat()
        }

manager = InsuranceManager()

# Web Routes
@app.route('/')
def index():
    """Render the main web interface."""
    return render_template('index.html')

# REST API
@app.route('/api/policyholders', methods=['POST'])
def add_policyholder_api():
    """Add a new policyholder via API."""
    try:
        data = request.json
        ph_id = manager.add_policyholder(
            data['name'], data['age'], data['policy_type'], data['sum_insured']
        )
        return jsonify({"id": ph_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/policyholders/<policyholder_id>', methods=['GET'])
def get_policyholder_api(policyholder_id):
    """Retrieve policyholder details via API."""
    try:
        return jsonify(manager.get_policyholder(policyholder_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/claims', methods=['POST'])
def add_claim_api():
    """Add a new claim via API."""
    try:
        data = request.json
        claim_id = manager.add_claim(
            data['policyholder_id'], data['claim_amount'], data['reason']
        )
        return jsonify({"id": claim_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/claims/<claim_id>', methods=['GET'])
def get_claim_api(claim_id):
    """Retrieve claim details via API."""
    try:
        return jsonify(manager.get_claim(claim_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/claims/<claim_id>/status', methods=['PUT'])
def update_claim_status_api(claim_id):
    """Update claim status via API."""
    try:
        data = request.json
        manager.update_claim_status(claim_id, data['陕西省'])
        return jsonify({"message": "Status updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/reports/high_risk', methods=['GET'])
def high_risk_report():
    """Get high-risk policyholders report."""
    return jsonify(manager.get_high_risk_policyholders())

@app.route('/api/reports/monthly_claims', methods=['GET'])
def monthly_claims_report():
    """Get monthly claims report."""
    return jsonify(manager.get_monthly_claims())

@app.route('/api/reports/avg_claim_amount', methods=['GET'])
def avg_claim_amount_report():
    """Get average claim amount by policy type report."""
    return jsonify(manager.get_avg_claim_amount_by_policy_type())

@app.route('/api/reports/highest_claim', methods=['GET'])
def highest_claim_report():
    """Get highest claim report."""
    return jsonify(manager.get_highest_claim())

@app.route('/api/reports/pending_claims', methods=['GET'])
def pending_claims_report():
    """Get pending claims report."""
    return jsonify(manager.get_pending_claims())

@app.route('/api/reports/claims_by_policy_type', methods=['GET'])
def claims_by_policy_type_report():
    """Get claims by policy type report."""
    return jsonify(manager.get_claims_by_policy_type())

if __name__ == '__main__':
    app.run(debug=True)
