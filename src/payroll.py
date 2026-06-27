"""
Canadian Payroll Deductions Calculator — 2026 (Alberta)

Based on CRA T4127 Payroll Deductions Formulas, 122nd Edition (Jan 1, 2026).
Semi-monthly pay periods (P=24), province = Alberta, Claim Code 1.
"""

# ---------------------------------------------------------------------------
# 2026 CONSTANTS
# ---------------------------------------------------------------------------

PAY_PERIODS = 24  # semi-monthly

# --- CPP (Canada Pension Plan) ---
CPP_RATE = 0.0595
CPP_BASIC_EXEMPTION = 3500.00
CPP_YMPE = 74600.00  # Year's Maximum Pensionable Earnings
CPP_MAX_ANNUAL = 4230.45
CPP_EXEMPTION_PER_PERIOD = CPP_BASIC_EXEMPTION / PAY_PERIODS  # $145.83

# --- CPP2 (second ceiling) ---
CPP2_RATE = 0.04
CPP2_YAMPE = 85000.00  # Year's Additional Maximum Pensionable Earnings
CPP2_MAX_ANNUAL = 416.00

# --- EI (Employment Insurance) ---
EI_EMPLOYEE_RATE = 0.0163
EI_EMPLOYER_MULTIPLIER = 1.4
EI_MIE = 68900.00  # Maximum Insurable Earnings
EI_MAX_ANNUAL = 1123.07

# --- Federal tax brackets (2026) ---
# (upper_threshold, rate)  — last bracket has no upper limit
FEDERAL_BRACKETS = [
    (58523.00, 0.14),
    (117045.00, 0.205),
    (181440.00, 0.26),
    (258482.00, 0.29),
    (float("inf"), 0.33),
]
FEDERAL_LOWEST_RATE = 0.14

# Federal Basic Personal Amount (BPA)
FEDERAL_BPA_MAX = 16452.00   # income <= $181,440
FEDERAL_BPA_MIN = 14829.00   # income >= $258,482
FEDERAL_BPA_PHASE_LOW = 181440.00
FEDERAL_BPA_PHASE_HIGH = 258482.00

# Canada Employment Amount (CEA)
CEA = 1501.00

# --- Alberta provincial tax brackets (2026) ---
ALBERTA_BRACKETS = [
    (61200.00, 0.08),
    (154259.00, 0.10),
    (185111.00, 0.12),
    (246813.00, 0.13),
    (370220.00, 0.14),
    (float("inf"), 0.15),
]
ALBERTA_LOWEST_RATE = 0.08
ALBERTA_BPA = 22769.00


def _build_k_table(brackets):

    table = []
    prev_rate = 0.0
    k = 0.0
    prev_threshold = 0.0
    for upper, rate in brackets:
        k = k + (rate - prev_rate) * prev_threshold
        table.append((upper, rate, round(k, 2)))
        prev_rate = rate
        prev_threshold = upper
    return table


FEDERAL_K = _build_k_table(FEDERAL_BRACKETS)
ALBERTA_K = _build_k_table(ALBERTA_BRACKETS)


def _bracket_lookup(table, annual_income):
    for upper, rate, k in table:
        if annual_income <= upper:
            return rate, k
    last = table[-1]
    return last[1], last[2]


def _federal_bpa(annual_income):
    if annual_income <= FEDERAL_BPA_PHASE_LOW:
        return FEDERAL_BPA_MAX
    if annual_income >= FEDERAL_BPA_PHASE_HIGH:
        return FEDERAL_BPA_MIN
    reduction = (annual_income - FEDERAL_BPA_PHASE_LOW) * (
        FEDERAL_BPA_MAX - FEDERAL_BPA_MIN
    ) / (FEDERAL_BPA_PHASE_HIGH - FEDERAL_BPA_PHASE_LOW)
    return FEDERAL_BPA_MAX - reduction


def calculate_payroll(gross_pay: float) -> dict:


    A = gross_pay * PAY_PERIODS  # annualized income

    # ---- CPP (employee) ----
    pensionable = min(gross_pay, CPP_YMPE / PAY_PERIODS)
    cpp = max(0.0, (pensionable - CPP_EXEMPTION_PER_PERIOD) * CPP_RATE)
    cpp = min(cpp, CPP_MAX_ANNUAL / PAY_PERIODS)

    # ---- CPP2 (employee) ----
    if A > CPP_YMPE:
        cpp2_base = min(A, CPP2_YAMPE) - CPP_YMPE
        cpp2_annual = min(cpp2_base * CPP2_RATE, CPP2_MAX_ANNUAL)
        cpp2 = cpp2_annual / PAY_PERIODS
    else:
        cpp2 = 0.0

    # ---- EI (employee) ----
    insurable = min(gross_pay, EI_MIE / PAY_PERIODS)
    ei = min(insurable * EI_EMPLOYEE_RATE, EI_MAX_ANNUAL / PAY_PERIODS)

    # ---- Annual deductible credits for tax calc ----
    annual_cpp = cpp * PAY_PERIODS
    annual_cpp2 = cpp2 * PAY_PERIODS
    annual_ei = ei * PAY_PERIODS

    # ---- Federal tax ----
    R, K = _bracket_lookup(FEDERAL_K, A)
    bpa = _federal_bpa(A)
    K1 = bpa * FEDERAL_LOWEST_RATE
    K2 = (annual_cpp + annual_cpp2 + annual_ei) * FEDERAL_LOWEST_RATE
    K3 = min(A, CEA) * FEDERAL_LOWEST_RATE

    federal_tax_annual = max(0.0, R * A - K - K1 - K2 - K3)
    federal_tax = federal_tax_annual / PAY_PERIODS

    # ---- Alberta provincial tax ----
    V, KP = _bracket_lookup(ALBERTA_K, A)
    K1P = ALBERTA_BPA * ALBERTA_LOWEST_RATE
    K2P = (annual_cpp + annual_cpp2 + annual_ei) * ALBERTA_LOWEST_RATE

    provincial_tax_annual = max(0.0, V * A - KP - K1P - K2P)
    provincial_tax = provincial_tax_annual / PAY_PERIODS

    # ---- Employee totals ----
    total_deductions = cpp + cpp2 + ei + federal_tax + provincial_tax
    net_pay = gross_pay - total_deductions

    # ---- Employer costs ----
    employer_cpp = cpp  # 1:1 match
    employer_cpp2 = cpp2
    employer_ei = ei * EI_EMPLOYER_MULTIPLIER
    total_employer_cost = gross_pay + employer_cpp + employer_cpp2 + employer_ei

    def r2(x):
        return round(x, 2)

    return {
        "gross_pay": r2(gross_pay),
        "federal_tax": r2(federal_tax),
        "provincial_tax": r2(provincial_tax),
        "cpp": r2(cpp),
        "cpp2": r2(cpp2),
        "ei": r2(ei),
        "total_deductions": r2(total_deductions),
        "net_pay": r2(net_pay),
        "employer_cpp": r2(employer_cpp),
        "employer_cpp2": r2(employer_cpp2),
        "employer_ei": r2(employer_ei),
        "total_employer_cost": r2(total_employer_cost),
        "annual_gross": r2(A),
    }


def format_payroll_report(teacher_name: str, gross_pay: float) -> str:


    r = calculate_payroll(gross_pay)

    lines = [
        f"📋 PAYROLL REPORT — {teacher_name.upper()}",
        f"   Job Title: Teacher | Province: Alberta | Pay frequency: Semi-monthly",
        f"   Pay period gross: ${r['gross_pay']:,.2f}  (annual: ${r['annual_gross']:,.2f})",
        "",
        "── Employee Deductions ────────────────────",
        f"   CPP contribution:         ${r['cpp']:>9,.2f}",
        f"   CPP2 contribution:        ${r['cpp2']:>9,.2f}",
        f"   EI premium:               ${r['ei']:>9,.2f}",
        f"   Federal income tax:       ${r['federal_tax']:>9,.2f}",
        f"   Provincial income tax:    ${r['provincial_tax']:>9,.2f}",
        f"   ─────────────────────────────────────",
        f"   Total deductions:         ${r['total_deductions']:>9,.2f}",
        "",
        f"   ✅ NET PAY:                ${r['net_pay']:>9,.2f}",
        "",
        "── Employer Contributions ────────────────",
        f"   Employer CPP:             ${r['employer_cpp']:>9,.2f}",
        f"   Employer CPP2:            ${r['employer_cpp2']:>9,.2f}",
        f"   Employer EI:              ${r['employer_ei']:>9,.2f}",
        "",
        f"   💰 TOTAL EMPLOYER COST:    ${r['total_employer_cost']:>9,.2f}",
    ]
    return "\n".join(lines)


def format_multi_teacher_report(teachers: list[dict]) -> str:

    sections = []
    totals = {
        "gross": 0.0, "federal_tax": 0.0, "provincial_tax": 0.0,
        "cpp": 0.0, "cpp2": 0.0, "ei": 0.0,
        "net_pay": 0.0, "employer_cpp": 0.0, "employer_cpp2": 0.0,
        "employer_ei": 0.0, "total_employer_cost": 0.0,
    }

    for t in teachers:
        sections.append(format_payroll_report(t["name"], t["gross_pay"]))
        r = calculate_payroll(t["gross_pay"])
        totals["gross"] += r["gross_pay"]
        totals["federal_tax"] += r["federal_tax"]
        totals["provincial_tax"] += r["provincial_tax"]
        totals["cpp"] += r["cpp"]
        totals["cpp2"] += r["cpp2"]
        totals["ei"] += r["ei"]
        totals["net_pay"] += r["net_pay"]
        totals["employer_cpp"] += r["employer_cpp"]
        totals["employer_cpp2"] += r["employer_cpp2"]
        totals["employer_ei"] += r["employer_ei"]
        totals["total_employer_cost"] += r["total_employer_cost"]

    separator = "\n\n" + "=" * 50 + "\n\n"
    report = separator.join(sections)

    report += "\n\n" + "=" * 50
    report += f"\n\n📊 PAYROLL SUMMARY — ALL TEACHERS ({len(teachers)} employees)"
    report += f"\n   Total gross pay:          ${totals['gross']:>10,.2f}"
    report += f"\n   Total federal tax:        ${totals['federal_tax']:>10,.2f}"
    report += f"\n   Total provincial tax:     ${totals['provincial_tax']:>10,.2f}"
    report += f"\n   Total CPP:                ${totals['cpp']:>10,.2f}"
    report += f"\n   Total CPP2:               ${totals['cpp2']:>10,.2f}"
    report += f"\n   Total EI:                 ${totals['ei']:>10,.2f}"
    report += f"\n   Total net pay:            ${totals['net_pay']:>10,.2f}"
    report += f"\n   Total employer CPP:       ${totals['employer_cpp']:>10,.2f}"
    report += f"\n   Total employer CPP2:      ${totals['employer_cpp2']:>10,.2f}"
    report += f"\n   Total employer EI:        ${totals['employer_ei']:>10,.2f}"
    report += f"\n   Total employer cost:      ${totals['total_employer_cost']:>10,.2f}"

    report += "\n\n⚠️ Based on CRA T4127 formulas (2026). Claim Code 1 (basic personal amount only)."
    report += "\n   Verify against CRA PDOC before processing actual payroll."

    return report
