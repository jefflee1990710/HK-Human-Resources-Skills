#!/usr/bin/env python3
"""
ADW Salary Calculator

Reads dynamic Excel workbook structure, infers columns/sheets, and computes
employee monthly payout using an ADW-based model.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


SHEET_ROLE_KEYWORDS: Dict[str, List[str]] = {
    "salary": ["salary", "payroll", "wage", "income", "compensation"],
    "attendance": ["attendance", "timesheet", "clock", "worklog", "duty"],
    "leave": ["leave", "holiday", "absence", "off"],
    "employee": ["employee", "staff", "worker", "personnel", "master"],
}


FIELD_ALIASES: Dict[str, List[str]] = {
    "employee_id": [
        "employee_id",
        "employeeid",
        "employee_no",
        "employee number",
        "staff id",
        "staff_no",
        "emp id",
        "empid",
        "工號",
        "員工編號",
    ],
    "employee_name": ["employee_name", "name", "employee", "staff name", "姓名", "員工姓名"],
    "month": ["month", "pay_month", "period", "yyyymm", "payroll month", "月份", "年月"],
    "date": ["date", "work_date", "day", "attendance date", "日期"],
    "base_salary": ["base_salary", "basic salary", "monthly salary", "底薪", "基本工資"],
    "allowance": ["allowance", "津貼"],
    "commission": ["commission", "佣金"],
    "bonus": ["bonus", "花紅", "獎金"],
    "deduction": ["deduction", "扣款", "adjustment minus"],
    "annual_leave_days": ["annual_leave_days", "annual leave", "al_days", "年假"],
    "sick_leave_days": ["sick_leave_days", "sick leave", "sl_days", "病假"],
    "sick_leave_45_days": ["sick_leave_45_days", "long sick leave", "paid sick 80", "病假4/5"],
    "sick_leave_full_days": ["sick_leave_full_days", "paid sick full", "病假全薪"],
    "maternity_leave_days": ["maternity_leave_days", "maternity", "產假"],
    "paternity_leave_days": ["paternity_leave_days", "paternity", "侍產假"],
    "unpaid_leave_days": ["unpaid_leave_days", "no pay leave", "unpaid leave", "np_days", "無薪假"],
    "no_pay_days": ["no_pay_days", "no pay", "lwp", "leave without pay"],
}


REQUIRED_BY_ROLE: Dict[str, List[str]] = {
    "salary": ["base_salary"],
    "attendance": [],
    "leave": [],
    "employee": [],
}


DEFAULT_POLICY = {
    "adw_lookback_months": 12,
    "long_sick_leave_multiplier": 0.8,
    "maternity_multiplier": 0.8,
    "paternity_multiplier": 0.8,
    "full_paid_sick_multiplier": 1.0,
}


@dataclass
class FieldMatch:
    field: str
    column: Optional[str]
    confidence: float
    alternatives: List[str]


def normalize_token(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[_\-\./]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == "":
        return 0.0
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_month(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Already looks like YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", s):
        return s

    dt = pd.to_datetime(s, errors="coerce")
    if pd.isna(dt):
        return None
    return f"{dt.year:04d}-{dt.month:02d}"


def months_before(target_month: str, lookback: int) -> List[str]:
    year, month = map(int, target_month.split("-"))
    months: List[str] = []
    y, m = year, month
    for _ in range(lookback):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")
    return sorted(months)


def score_column(field: str, column_name: str) -> float:
    norm_col = normalize_token(column_name)
    aliases = FIELD_ALIASES.get(field, [field])
    best = 0.0
    for alias in aliases:
        norm_alias = normalize_token(alias)
        if norm_col == norm_alias:
            best = max(best, 1.0)
            continue
        if norm_alias in norm_col:
            best = max(best, 0.85)
            continue
        alias_tokens = set(norm_alias.split(" "))
        col_tokens = set(norm_col.split(" "))
        if not alias_tokens:
            continue
        overlap = len(alias_tokens.intersection(col_tokens)) / len(alias_tokens)
        best = max(best, 0.4 + overlap * 0.5)
    return min(best, 1.0)


def pick_best_columns(columns: List[str], fields: List[str]) -> Dict[str, FieldMatch]:
    result: Dict[str, FieldMatch] = {}
    for field in fields:
        scored: List[Tuple[str, float]] = [(col, score_column(field, col)) for col in columns]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_col, top_score = scored[0] if scored else (None, 0.0)
        alternatives = [c for c, _ in scored[:4]]
        chosen = top_col if top_score >= 0.55 else None
        result[field] = FieldMatch(
            field=field,
            column=chosen,
            confidence=round(top_score, 3),
            alternatives=alternatives,
        )
    return result


def infer_sheet_role(sheet_name: str, columns: List[str]) -> str:
    text = normalize_token(sheet_name + " " + " ".join(columns))
    role_scores: Dict[str, float] = {k: 0.0 for k in SHEET_ROLE_KEYWORDS}
    for role, words in SHEET_ROLE_KEYWORDS.items():
        for w in words:
            if normalize_token(w) in text:
                role_scores[role] += 1.0
    # Additional hints from field matching.
    if any(score_column("base_salary", c) > 0.8 for c in columns):
        role_scores["salary"] += 2.0
    if any(score_column("date", c) > 0.8 for c in columns):
        role_scores["attendance"] += 1.5
    if any(score_column("annual_leave_days", c) > 0.7 for c in columns):
        role_scores["leave"] += 1.5

    best_role = max(role_scores, key=role_scores.get)
    return best_role


def load_workbook(path: Path) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path)
    wb: Dict[str, pd.DataFrame] = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        wb[sheet] = df
    return wb


def choose_primary_key(mapping: Dict[str, FieldMatch]) -> Optional[str]:
    by_id = mapping.get("employee_id")
    by_name = mapping.get("employee_name")
    if by_id and by_id.column:
        return "employee_id"
    if by_name and by_name.column:
        return "employee_name"
    return None


def interactive_confirm(mapping_report: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    overrides: Dict[str, Dict[str, str]] = {}
    print("\n[Interactive Mapping Confirmation]")
    print("Press ENTER to keep inferred value.\n")

    for role in mapping_report["roles"]:
        role_name = role["role"]
        role_sheet = role["sheet"]
        field_matches = role["fields"]
        overrides[role_name] = {}

        print(f"\nRole: {role_name} | Sheet: {role_sheet}")
        for field, meta in field_matches.items():
            current = meta["column"]
            alternatives = meta["alternatives"]
            confidence = meta["confidence"]
            print(f"- Field: {field} | inferred: {current} | confidence: {confidence}")
            if alternatives:
                print(f"  Alternatives: {alternatives}")
            answer = input("  Override column (blank to keep): ").strip()
            if answer:
                overrides[role_name][field] = answer
            elif current:
                overrides[role_name][field] = current
    return overrides


def apply_mapping_overrides(
    mapping_report: Dict[str, Any],
    manual_mapping: Optional[Dict[str, Dict[str, str]]],
) -> Dict[str, Dict[str, str]]:
    final_mapping: Dict[str, Dict[str, str]] = {}
    for role_data in mapping_report["roles"]:
        role = role_data["role"]
        final_mapping[role] = {}
        for field, info in role_data["fields"].items():
            inferred = info["column"]
            if manual_mapping and role in manual_mapping and field in manual_mapping[role]:
                final_mapping[role][field] = manual_mapping[role][field]
            elif inferred:
                final_mapping[role][field] = inferred
    return final_mapping


def ensure_month_column(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.Series:
    month_col = mapping.get("month")
    if month_col and month_col in df.columns:
        return df[month_col].apply(parse_month)

    date_col = mapping.get("date")
    if date_col and date_col in df.columns:
        return df[date_col].apply(parse_month)

    return pd.Series([None] * len(df))


def aggregate_salary(
    salary_df: pd.DataFrame,
    salary_mapping: Dict[str, str],
    key_field: str,
) -> pd.DataFrame:
    key_col = salary_mapping[key_field]
    month_series = ensure_month_column(salary_df, salary_mapping)
    temp = salary_df.copy()
    temp["_month"] = month_series

    base_col = salary_mapping.get("base_salary")
    allowance_col = salary_mapping.get("allowance")
    commission_col = salary_mapping.get("commission")
    bonus_col = salary_mapping.get("bonus")
    deduction_col = salary_mapping.get("deduction")

    for col in [base_col, allowance_col, commission_col, bonus_col, deduction_col]:
        if col and col in temp.columns:
            temp[col] = temp[col].apply(to_float)

    temp["eligible_wages"] = 0.0
    if base_col and base_col in temp.columns:
        temp["eligible_wages"] += temp[base_col]
    if allowance_col and allowance_col in temp.columns:
        temp["eligible_wages"] += temp[allowance_col]
    if commission_col and commission_col in temp.columns:
        temp["eligible_wages"] += temp[commission_col]
    if bonus_col and bonus_col in temp.columns:
        temp["eligible_wages"] += temp[bonus_col]
    if deduction_col and deduction_col in temp.columns:
        temp["eligible_wages"] -= temp[deduction_col]

    group = (
        temp.groupby([key_col, "_month"], dropna=False)["eligible_wages"]
        .sum()
        .reset_index()
        .rename(columns={key_col: "employee_key", "_month": "month"})
    )
    return group


def aggregate_leave_days(
    leave_df: pd.DataFrame,
    leave_mapping: Dict[str, str],
    key_field: str,
) -> pd.DataFrame:
    key_col = leave_mapping[key_field]
    month_series = ensure_month_column(leave_df, leave_mapping)
    temp = leave_df.copy()
    temp["_month"] = month_series

    fields = [
        "annual_leave_days",
        "sick_leave_days",
        "sick_leave_45_days",
        "sick_leave_full_days",
        "maternity_leave_days",
        "paternity_leave_days",
        "unpaid_leave_days",
        "no_pay_days",
    ]
    prepared: Dict[str, pd.Series] = {}
    for field in fields:
        col = leave_mapping.get(field)
        if col and col in temp.columns:
            prepared[field] = temp[col].apply(to_float)
        else:
            prepared[field] = pd.Series([0.0] * len(temp))

    for field, series in prepared.items():
        temp[field] = series

    group = (
        temp.groupby([key_col, "_month"], dropna=False)[fields]
        .sum()
        .reset_index()
        .rename(columns={key_col: "employee_key", "_month": "month"})
    )
    return group


def derive_counted_days(
    month: str,
    leave_row: Optional[pd.Series],
) -> float:
    y, m = map(int, month.split("-"))
    calendar_days = float(calendar.monthrange(y, m)[1])
    if leave_row is None:
        return calendar_days

    excluded = (
        to_float(leave_row.get("unpaid_leave_days", 0.0))
        + to_float(leave_row.get("no_pay_days", 0.0))
        + to_float(leave_row.get("maternity_leave_days", 0.0))
        + to_float(leave_row.get("paternity_leave_days", 0.0))
    )
    return max(0.0, calendar_days - excluded)


def calculate_for_employee(
    employee_key: str,
    target_month: str,
    salary_hist: pd.DataFrame,
    leave_hist: pd.DataFrame,
    policy: Dict[str, float],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    lookback_months = months_before(target_month, int(policy["adw_lookback_months"]))

    salary_rows = salary_hist[salary_hist["employee_key"] == employee_key]
    leave_rows = leave_hist[leave_hist["employee_key"] == employee_key]

    total_eligible = 0.0
    total_counted_days = 0.0
    months_used = 0

    for month in lookback_months:
        sr = salary_rows[salary_rows["month"] == month]
        if sr.empty:
            continue
        wage = to_float(sr["eligible_wages"].sum())
        lr = leave_rows[leave_rows["month"] == month]
        leave_row = None if lr.empty else lr.iloc[0]
        counted_days = derive_counted_days(month, leave_row)
        total_eligible += wage
        total_counted_days += counted_days
        months_used += 1

    if months_used == 0:
        warnings.append(
            f"{employee_key}: no historical salary data in lookback window; ADW fallback to target month estimate."
        )
        sr_target = salary_rows[salary_rows["month"] == target_month]
        fallback_wage = to_float(sr_target["eligible_wages"].sum())
        y, m = map(int, target_month.split("-"))
        total_eligible = fallback_wage
        total_counted_days = float(calendar.monthrange(y, m)[1])

    adw = (total_eligible / total_counted_days) if total_counted_days > 0 else 0.0

    sr_target = salary_rows[salary_rows["month"] == target_month]
    base_current = to_float(sr_target["eligible_wages"].sum())
    lr_target = leave_rows[leave_rows["month"] == target_month]
    leave_target = None if lr_target.empty else lr_target.iloc[0]

    annual_leave_days = to_float(leave_target.get("annual_leave_days", 0.0)) if leave_target is not None else 0.0
    sick_leave_45_days = to_float(leave_target.get("sick_leave_45_days", 0.0)) if leave_target is not None else 0.0
    sick_leave_full_days = to_float(leave_target.get("sick_leave_full_days", 0.0)) if leave_target is not None else 0.0
    maternity_days = to_float(leave_target.get("maternity_leave_days", 0.0)) if leave_target is not None else 0.0
    paternity_days = to_float(leave_target.get("paternity_leave_days", 0.0)) if leave_target is not None else 0.0
    unpaid_days = 0.0
    if leave_target is not None:
        unpaid_days = to_float(leave_target.get("unpaid_leave_days", 0.0)) + to_float(leave_target.get("no_pay_days", 0.0))

    annual_leave_pay = adw * annual_leave_days
    sick_leave_45_pay = adw * sick_leave_45_days * float(policy["long_sick_leave_multiplier"])
    sick_leave_full_pay = adw * sick_leave_full_days * float(policy["full_paid_sick_multiplier"])
    maternity_pay = adw * maternity_days * float(policy["maternity_multiplier"])
    paternity_pay = adw * paternity_days * float(policy["paternity_multiplier"])
    unpaid_deduction = adw * unpaid_days * -1.0

    payout = (
        base_current
        + annual_leave_pay
        + sick_leave_45_pay
        + sick_leave_full_pay
        + maternity_pay
        + paternity_pay
        + unpaid_deduction
    )

    summary = {
        "employee_key": employee_key,
        "target_month": target_month,
        "adw": round(adw, 4),
        "lookback_months_used": months_used,
        "lookback_total_eligible_wages": round(total_eligible, 2),
        "lookback_total_counted_days": round(total_counted_days, 2),
        "target_base_component": round(base_current, 2),
        "total_payout": round(payout, 2),
    }

    breakdown = [
        {"employee_key": employee_key, "month": target_month, "component": "base_salary_component", "value": round(base_current, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "annual_leave_pay", "value": round(annual_leave_pay, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "sick_leave_45_pay", "value": round(sick_leave_45_pay, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "sick_leave_full_pay", "value": round(sick_leave_full_pay, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "maternity_pay", "value": round(maternity_pay, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "paternity_pay", "value": round(paternity_pay, 2)},
        {"employee_key": employee_key, "month": target_month, "component": "unpaid_leave_deduction", "value": round(unpaid_deduction, 2)},
    ]
    return summary, breakdown, warnings


def build_mapping_report(workbook: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    roles: Dict[str, Dict[str, Any]] = {}

    for sheet_name, df in workbook.items():
        columns = [str(c) for c in df.columns]
        role = infer_sheet_role(sheet_name, columns)
        fields = list(FIELD_ALIASES.keys())
        field_matches = pick_best_columns(columns, fields)

        role_data = roles.get(role)
        if role_data is None:
            roles[role] = {
                "role": role,
                "sheet": sheet_name,
                "fields": {f: vars(m) for f, m in field_matches.items()},
            }
        else:
            # Keep the sheet that has stronger base salary/employee match.
            current_score = role_data["fields"]["base_salary"]["confidence"] + role_data["fields"]["employee_id"]["confidence"]
            new_score = field_matches["base_salary"].confidence + field_matches["employee_id"].confidence
            if new_score > current_score:
                roles[role] = {
                    "role": role,
                    "sheet": sheet_name,
                    "fields": {f: vars(m) for f, m in field_matches.items()},
                }

    # Ensure all roles exist to simplify downstream logic.
    for role in SHEET_ROLE_KEYWORDS.keys():
        if role not in roles:
            roles[role] = {"role": role, "sheet": None, "fields": {}}

    role_list = [roles[r] for r in ["salary", "attendance", "leave", "employee"]]
    mapping_report = {"roles": role_list}
    return mapping_report


def build_questions(mapping_report: Dict[str, Any]) -> List[str]:
    questions: List[str] = []
    for role_data in mapping_report["roles"]:
        role = role_data["role"]
        sheet = role_data["sheet"]
        fields = role_data["fields"]

        if sheet is None:
            questions.append(f"Missing {role} sheet. Please confirm which sheet should be used as {role}.")
            continue

        for req in REQUIRED_BY_ROLE.get(role, []):
            info = fields.get(req, {})
            if not info.get("column"):
                questions.append(
                    f"Sheet '{sheet}' missing required field '{req}'. Please provide the correct column name."
                )
            elif info.get("confidence", 0.0) < 0.75:
                questions.append(
                    f"Field '{req}' on sheet '{sheet}' has low confidence ({info.get('confidence')}). "
                    f"Please confirm the correct column."
                )

        # Primary employee key checks for salary/leave.
        if role in {"salary", "leave", "attendance"}:
            employee_id = fields.get("employee_id", {}).get("column")
            employee_name = fields.get("employee_name", {}).get("column")
            if not employee_id and not employee_name:
                questions.append(
                    f"Sheet '{sheet}' has no clear employee identifier. Please specify employee ID or name column."
                )
    return questions


def load_manual_mapping(path: Optional[Path]) -> Optional[Dict[str, Dict[str, str]]]:
    if not path:
        return None
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("mapping-json must be an object {role: {field: column}}")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate ADW-based monthly salary payout from dynamic Excel files.")
    parser.add_argument("--input", required=True, help="Path to input Excel file.")
    parser.add_argument("--month", required=True, help="Target payroll month in YYYY-MM.")
    parser.add_argument("--output-dir", default="output", help="Directory for generated output files.")
    parser.add_argument("--mapping-json", help="Optional JSON path for manual column mapping overrides.")
    parser.add_argument("--interactive", action="store_true", help="Interactive terminal mode for mapping confirmation.")
    parser.add_argument("--report-only", action="store_true", help="Only infer schema and generate mapping report/questions.")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook = load_workbook(input_path)
    mapping_report = build_mapping_report(workbook)
    questions = build_questions(mapping_report)

    mapping_report_path = output_dir / "mapping_report.json"
    questions_path = output_dir / "questions_for_user.txt"

    with mapping_report_path.open("w", encoding="utf-8") as f:
        json.dump(mapping_report, f, ensure_ascii=False, indent=2)

    with questions_path.open("w", encoding="utf-8") as f:
        if questions:
            f.write("\n".join(questions))
        else:
            f.write("No blocking mapping questions detected.")

    print(f"[OK] Mapping report: {mapping_report_path}")
    print(f"[OK] Questions: {questions_path}")

    if args.report_only:
        print("[INFO] Report-only mode complete.")
        return

    manual_mapping = load_manual_mapping(Path(args.mapping_json).expanduser().resolve()) if args.mapping_json else None
    if args.interactive:
        manual_mapping = interactive_confirm(mapping_report)

    final_mapping = apply_mapping_overrides(mapping_report, manual_mapping)

    if "salary" not in final_mapping or "base_salary" not in final_mapping["salary"]:
        raise ValueError("Unable to map required salary.base_salary column. Run with --interactive or provide --mapping-json.")

    salary_sheet = next((r["sheet"] for r in mapping_report["roles"] if r["role"] == "salary"), None)
    leave_sheet = next((r["sheet"] for r in mapping_report["roles"] if r["role"] == "leave"), None)

    salary_df = workbook[salary_sheet] if salary_sheet else pd.DataFrame()
    leave_df = workbook[leave_sheet] if leave_sheet else pd.DataFrame()

    salary_mapping = final_mapping.get("salary", {})
    leave_mapping = final_mapping.get("leave", {})

    key_field = "employee_id" if "employee_id" in salary_mapping else "employee_name"
    if key_field not in salary_mapping:
        raise ValueError("Unable to find salary employee identifier column (employee_id/employee_name).")

    # For leave sheet, align key if missing.
    if key_field not in leave_mapping:
        alt = "employee_name" if key_field == "employee_id" else "employee_id"
        if alt in leave_mapping:
            key_field_leave = alt
        else:
            key_field_leave = key_field
    else:
        key_field_leave = key_field

    salary_hist = aggregate_salary(salary_df, salary_mapping, key_field=key_field)
    if leave_df.empty:
        leave_hist = pd.DataFrame(columns=["employee_key", "month"])
    else:
        leave_hist = aggregate_leave_days(leave_df, leave_mapping, key_field=key_field_leave)

    # Align leave key column name.
    if not leave_hist.empty and key_field_leave != key_field:
        # Build a basic bridge if both fields exist in salary mapping and leave mapping.
        bridge_salary_col = salary_mapping.get(key_field)
        bridge_leave_col = leave_mapping.get(key_field_leave)
        if bridge_salary_col and bridge_leave_col and key_field != key_field_leave:
            pass

    employee_keys = sorted(salary_hist["employee_key"].dropna().astype(str).unique().tolist())
    summaries: List[Dict[str, Any]] = []
    breakdown_rows: List[Dict[str, Any]] = []
    warning_rows: List[Dict[str, Any]] = []

    for emp_key in employee_keys:
        summary, breakdown, warnings = calculate_for_employee(
            employee_key=emp_key,
            target_month=args.month,
            salary_hist=salary_hist,
            leave_hist=leave_hist,
            policy=DEFAULT_POLICY,
        )
        summaries.append(summary)
        breakdown_rows.extend(breakdown)
        for w in warnings:
            warning_rows.append({"employee_key": emp_key, "warning": w})

    summary_df = pd.DataFrame(summaries)
    breakdown_df = pd.DataFrame(breakdown_rows)
    warnings_df = pd.DataFrame(warning_rows)

    summary_path = output_dir / "employee_payout_summary.csv"
    breakdown_path = output_dir / "employee_payout_breakdown.csv"
    adw_path = output_dir / "employee_adw_details.csv"
    warnings_path = output_dir / "calculation_warnings.csv"

    summary_df.to_csv(summary_path, index=False)
    breakdown_df.to_csv(breakdown_path, index=False)
    summary_df[
        [
            "employee_key",
            "target_month",
            "adw",
            "lookback_months_used",
            "lookback_total_eligible_wages",
            "lookback_total_counted_days",
        ]
    ].to_csv(adw_path, index=False)
    warnings_df.to_csv(warnings_path, index=False)

    print(f"[OK] Summary: {summary_path}")
    print(f"[OK] Breakdown: {breakdown_path}")
    print(f"[OK] ADW details: {adw_path}")
    print(f"[OK] Warnings: {warnings_path}")


if __name__ == "__main__":
    main()
