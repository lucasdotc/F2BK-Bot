"""Draft pay stub emails (.eml) with a PDOC-style PDF attached, one per employee."""

from datetime import date
from email.message import EmailMessage

from fpdf import FPDF

from src.payroll import (
    ALBERTA_BPA, CPP_BASE_RATE, CPP_MAX_ANNUAL, CPP_RATE, CPP2_MAX_ANNUAL,
    FEDERAL_BPA_MAX, calculate_payroll,
)

EMPLOYER = "Free to be Kidz Early Learning Center"
SENDER = "F2BK Agent <f2bkagent@gmail.com>"
SIGNATURE = "Karina Carvalho"


def _ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _money(x: float) -> str:
    return f"{x:,.2f}"


def _period_start(pay_date: date) -> int:
    return 1 if pay_date.day <= 15 else 16


def pdf_filename(name: str, pay_date: date) -> str:
    return f"{name}-(EE & ER)-PDOC-Date paid-{pay_date.isoformat()}.pdf"


def build_paystub_pdf(name: str, pay_date: date, gross_pay: float) -> bytes:
    r = calculate_payroll(gross_pay)
    cpp_additional = round(r["cpp"] * (CPP_RATE - CPP_BASE_RATE) / CPP_RATE, 2)
    tax = round(r["federal_tax"] + r["provincial_tax"], 2)
    paid = f"{pay_date.isoformat()} (YYYY-MM-DD)"
    fname = pdf_filename(name, pay_date)

    pdf = FPDF(format="letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(15, 12)

    def row(label, value="", col=3, bold=False, indent=0):
        # col: 1 = left value column, 2 = middle, 3 = right (matches PDOC's three columns)
        pdf.set_font("Helvetica", "B" if bold else "", 9)
        pdf.set_x(15 + indent)
        pdf.cell(110 - indent, 5.5, label)
        x = {1: 125, 2: 145, 3: 170}[col]
        pdf.set_x(x - 30)
        pdf.cell(30, 5.5, value, align="R" if col != 1 else "L", new_x="LMARGIN", new_y="NEXT")

    def kv(label, value):
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(110, 5.5, label)
        pdf.cell(0, 5.5, value, new_x="LMARGIN", new_y="NEXT")

    def header(title, subtitle=None):
        pdf.add_page()
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, fname, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, title, align="C", new_x="LMARGIN", new_y="NEXT")
        if subtitle:
            pdf.cell(0, 6, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    def footer(page):
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(70, 5, "Created by the F2BK payroll calculator (CRA T4127 formulas)")
        pdf.cell(50, 5, f"Page {page} of 2", align="C")
        pdf.cell(0, 5, f"Saved on {pay_date.isoformat()}", align="R")

    # ---- Page 1: Result ----
    header("Payroll Deductions Calculator", "Result")
    kv("Employee's name:", name)
    kv("Employer's name:", EMPLOYER)
    kv("Pay period frequency:", "Semi-monthly (24 pay periods a year)")
    kv("Date the employee is paid:", paid)
    kv("Province of employment:", "Alberta")
    kv("Federal amount from TD1:", _money(FEDERAL_BPA_MAX))
    kv("Provincial amount from TD1:", _money(ALBERTA_BPA))
    pdf.ln(3)
    row("Salary or wages income", _money(r["gross_pay"]), col=2)
    row("Total cash income", _money(r["gross_pay"]), col=3, bold=True)
    pdf.ln(2)
    row("Federal tax deduction", _money(r["federal_tax"]), col=1)
    row("Provincial tax deduction", _money(r["provincial_tax"]), col=1)
    row("Total tax deductions on income", _money(tax), col=2)
    row("CPP deductions", _money(r["cpp"]), col=2)
    row("CPP2 deductions", _money(r["cpp2"]), col=2)
    row("EI deductions", _money(r["ei"]), col=2)
    row("Total deductions", _money(r["total_deductions"]), col=3, bold=True)
    row("Net amount", _money(r["net_pay"]), col=3, bold=True)
    pdf.ln(3)
    row("Other Amounts", bold=True)
    row("Deductions for CPP additional contribution", _money(cpp_additional), col=2)
    row("Taxable income for the pay period", _money(r["gross_pay"] - cpp_additional), col=2)
    row("Pensionable earnings for the pay period", _money(r["gross_pay"]), col=2)
    row("Insurable earnings for the pay period", _money(r["gross_pay"]), col=2)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(95, 5.5, "Year-to-Date Amounts")
    pdf.cell(35, 5.5, "Inputted Value", align="R")
    pdf.cell(0, 5.5, "Total for this Record", align="R", new_x="LMARGIN", new_y="NEXT")
    # shortcut: YTD inputs are always 0.00 because payroll.py has no YTD tracking; add YTD when it does.
    for label, total in [
        ("Pensionable earnings", r["gross_pay"]), ("CPP contributions", r["cpp"]),
        ("CPP2 contributions", r["cpp2"]), ("Insurable earnings", r["gross_pay"]),
        ("EI premiums", r["ei"]),
    ]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(95, 5.5, label)
        pdf.cell(35, 5.5, "0.00", align="R")
        pdf.cell(0, 5.5, _money(total), align="R", new_x="LMARGIN", new_y="NEXT")
    footer(1)

    # ---- Page 2: Employer Remittance Summary ----
    header("Employer Remittance Summary")
    kv("Employee's name:", name)
    kv("Date the employee is paid:", paid)
    pdf.ln(3)
    row("Canada Pension Plan (CPP)", bold=True)
    row("Employee CPP contributions", _money(r["cpp"]), col=2, indent=5)
    row("Employee CPP2 contributions", _money(r["cpp2"]), col=2, indent=5)
    row("Employer CPP contributions", _money(r["employer_cpp"]), col=2, indent=5)
    row("Employer CPP2 contributions", _money(r["employer_cpp2"]), col=2, indent=5)
    cpp_sub = r["cpp"] + r["cpp2"] + r["employer_cpp"] + r["employer_cpp2"]
    row("Subtotal of Canada Pension Plan (CPP)", _money(cpp_sub), col=3)
    row("Employment Insurance (EI)", bold=True)
    row("Employee EI contributions", _money(r["ei"]), col=2, indent=5)
    row("Employer EI contributions", _money(r["employer_ei"]), col=2, indent=5)
    row("Subtotal of Employment Insurance (EI)", _money(r["ei"] + r["employer_ei"]), col=3)
    row("Tax deductions", _money(tax), col=3)
    row("For this calculation, remit this amount", _money(r["remittance"]), col=3, bold=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4, (
        f"Based on pensionable months entered, the employee and employer Canada Pension Plan contribution "
        f"maximum for the year is ${_money(CPP_MAX_ANNUAL)}. If the employee's YMPE is reached, the CPP2 "
        f"contributions are required. Based on pensionable months entered, the employee and employer CPP2 "
        f"contribution maximum for the year is ${_money(CPP2_MAX_ANNUAL)}."
    ))
    footer(2)

    return bytes(pdf.output())


def build_paystub_email(
    name: str,
    to: str,
    pay_date: date,
    rate: float,
    top_up_rate: float,
    hours: float,
    vacation_total: float,
    vacation_used: float,
) -> EmailMessage:
    base = round(rate * hours, 2)
    topup = round(top_up_rate * hours, 2)
    gross = round(base + topup, 2)
    r = calculate_payroll(gross)

    first = name.split()[0]
    mon = pay_date.strftime("%b")
    short_date = f"{pay_date.day}-{mon}"
    period = f"{mon} {_ordinal(_period_start(pay_date))} to {_ordinal(pay_date.day)}"
    num = lambda x: f"{x:g}"  # 102.0 -> "102", 7.5 -> "7.5"

    body = f"""Hi {first},

Attached you'll find the pay stub for the period between {period}

Please see summary below:

Staff
 {name}
Pay date
{short_date}
Rate
 $ {_money(rate)}
Top Up Rate
 $ {_money(top_up_rate)}
Pay date
{short_date}
Hours
{num(hours)}
Base Salary
 $ {_money(base)}
Teaching
{num(hours)}
Topup Salary
 $ {_money(topup)}
Total
 $ {_money(r["gross_pay"])}
Employee Taxes
 $ {_money(r["total_deductions"])}
Net pay
 $ {_money(r["net_pay"])}
Vacation Hours {pay_date.year}
{num(vacation_total)}
 Used to date
{num(vacation_used)}
 Available Hours
{num(vacation_total - vacation_used)}



You should be receiving an e-transfer shortly.

Thank you so very much for all your help so far this month.  Very much appreciated


Best Regards,

{SIGNATURE}
"""

    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = f"F2bk - Pay Stub - {name} - {mon} {_ordinal(pay_date.day)} {pay_date.year}"
    msg["X-Unsent"] = "1"  # Outlook / Apple Mail open the .eml as an editable draft
    msg.set_content(body)
    msg.add_attachment(
        build_paystub_pdf(name, pay_date, gross),
        maintype="application", subtype="pdf", filename=pdf_filename(name, pay_date),
    )
    return msg


# Columns read from the uploaded CSV/XLSX (header match ignores case and spaces).
CSV_COLUMNS = {
    "name": "Staff", "email": "Email", "pay_date": "Pay Date", "rate": "Rate",
    "top_up_rate": "Top Up Rate", "hours": "Hours",
    "vacation_total": "Vacation Hours", "vacation_used": "Used to date",
}


def drafts_from_rows(rows: list[list]) -> tuple[list[EmailMessage], list[str]]:
    """Every value comes from the file itself; a missing column or blank cell is an error, never a default.
    The one exception is Email: a row without one is skipped (returned in the second list), never emailed."""
    norm = lambda s: str(s).strip().lower()
    header = [norm(h) for h in rows[0]]
    missing = [c for k, c in CSV_COLUMNS.items() if k != "email" and norm(c) not in header]
    if missing:
        raise ValueError(f"Colunas faltando no arquivo: {', '.join(missing)}")
    idx = {k: header.index(norm(c)) for k, c in CSV_COLUMNS.items() if norm(c) in header}

    drafts, skipped = [], []
    for n, row in enumerate(rows[1:], start=2):
        v = {k: str(row[i]).strip() if i < len(row) else "" for k, i in idx.items()}
        if not v.get("email"):
            skipped.append(v["name"] or f"Linha {n}")
            continue
        blank = [CSV_COLUMNS[k] for k, x in v.items() if not x]
        if blank:
            raise ValueError(f"Linha {n}: valores vazios em {', '.join(blank)}")
        try:
            paid = date.fromisoformat(v["pay_date"][:10])  # xlsx dates arrive as "YYYY-MM-DD 00:00:00"
            nums = {k: float(v[k].replace("$", "").replace(",", "")) for k in
                    ("rate", "top_up_rate", "hours", "vacation_total", "vacation_used")}
        except ValueError as e:
            raise ValueError(f"Linha {n} ({v['name']}): {e}") from None
        drafts.append(build_paystub_email(v["name"], v["email"], paid, **nums))
    return drafts, skipped


if __name__ == "__main__":
    # Self-check against the real Oct 15 2026 stub for Letícia França.
    m = build_paystub_email("Letícia França", "employee@example.com", date(2026, 10, 15),
                            23.00, 8.62, 102, 160, 152)
    text = m.get_body().get_content()
    for expected in ["Hi Letícia,", "between Oct 1st to 15th", "$ 2,346.00", "$ 879.24",
                     "$ 3,225.24", "$ 777.42", "$ 2,447.82", "Available Hours\n8\n"]:
        assert expected in text, expected
    assert m["Subject"] == "F2bk - Pay Stub - Letícia França - Oct 15th 2026", m["Subject"]
    with open("paystub_draft_example.eml", "wb") as f:
        f.write(bytes(m))
    print("ok -> paystub_draft_example.eml")
