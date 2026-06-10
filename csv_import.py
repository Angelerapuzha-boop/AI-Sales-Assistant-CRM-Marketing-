import io
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Company, Contact, User


REQUIRED_COMPANY_COLUMNS = {"name"}
REQUIRED_CONTACT_COLUMNS = {"first_name", "last_name"}


def validate_company_row(row: dict) -> list[str]:
    errors = []
    if not row.get("name"):
        errors.append("Company name is required")
    if row.get("revenue"):
        try:
            float(row["revenue"])
        except (ValueError, TypeError):
            errors.append("Invalid revenue value")
    if row.get("employee_count"):
        try:
            int(row["employee_count"])
        except (ValueError, TypeError):
            errors.append("Invalid employee_count value")
    return errors


def validate_contact_row(row: dict) -> list[str]:
    errors = []
    if not row.get("first_name"):
        errors.append("First name is required")
    if not row.get("last_name"):
        errors.append("Last name is required")
    return errors


def import_companies_csv(db: Session, user: User, file_content: bytes) -> dict[str, Any]:
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    imported = 0
    errors = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = validate_company_row(row_dict)
        if row_errors:
            errors.append({"row": idx + 2, "errors": row_errors})
            continue
        try:
            company = Company(
                owner_id=user.id,
                name=str(row_dict["name"]).strip(),
                industry=str(row_dict.get("industry", "")).strip() or None,
                website=str(row_dict.get("website", "")).strip() or None,
                revenue=float(row_dict["revenue"]) if pd.notna(row_dict.get("revenue")) else None,
                employee_count=int(row_dict["employee_count"]) if pd.notna(row_dict.get("employee_count")) else None,
                description=str(row_dict.get("description", "")).strip() or None,
                phone=str(row_dict.get("phone", "")).strip() or None,
            )
            db.add(company)
            imported += 1
        except Exception as e:
            errors.append({"row": idx + 2, "errors": [str(e)]})

    if imported:
        db.commit()

    return {"imported": imported, "errors": errors, "total_rows": len(df)}


def import_contacts_csv(db: Session, user: User, file_content: bytes) -> dict[str, Any]:
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    imported = 0
    errors = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = validate_contact_row(row_dict)
        if row_errors:
            errors.append({"row": idx + 2, "errors": row_errors})
            continue

        company_id = None
        if pd.notna(row_dict.get("company_id")):
            try:
                company_id = UUID(str(row_dict["company_id"]))
            except ValueError:
                errors.append({"row": idx + 2, "errors": ["Invalid company_id UUID"]})
                continue

        try:
            contact = Contact(
                owner_id=user.id,
                company_id=company_id,
                first_name=str(row_dict["first_name"]).strip(),
                last_name=str(row_dict["last_name"]).strip(),
                email=str(row_dict.get("email", "")).strip() or None,
                phone=str(row_dict.get("phone", "")).strip() or None,
                title=str(row_dict.get("title", "")).strip() or None,
                seniority=str(row_dict.get("seniority", "")).strip() or None,
            )
            db.add(contact)
            imported += 1
        except Exception as e:
            errors.append({"row": idx + 2, "errors": [str(e)]})

    if imported:
        db.commit()

    return {"imported": imported, "errors": errors, "total_rows": len(df)}
