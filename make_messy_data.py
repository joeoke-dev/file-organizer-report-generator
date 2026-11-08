"""Generate a small, deliberately messy sales CSV to demonstrate the cleaner.

Problems added on purpose: messy headers, extra spaces, inconsistent capitalization,
mixed date formats, currency symbols, placeholders like N/A, missing values,
negative quantities, exact duplicates, and a repeated order ID.
"""

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

REGIONS = ["Lagos", "Abuja", "Ibadan", "Kano", "Port Harcourt"]
CATEGORIES = ["Electronics", "Clothing", "Groceries", "Home"]
CUSTOMERS = ["Ada Obi", "Tunde Bello", "Chioma Eze", "Musa Danjuma", "Ngozi Okafor", "Seun Adeyemi"]
PRICE_RANGE = {"Electronics": (150, 900), "Clothing": (20, 120), "Groceries": (5, 60), "Home": (30, 300)}


def messy_text(value):
    value = random.choice([value, value, value.lower(), value.upper()])
    return random.choice([value, f"  {value}", f"{value}  ", value])


def messy_date(d):
    return random.choice([d.isoformat(), d.strftime("%d/%m/%Y"), d.strftime("%B %d, %Y")])


def messy_price(p):
    return random.choice([f"{p:.2f}", f"${p:,.2f}", f"{p:.2f}"])


def build_rows(n=120):
    rows = []
    start = date(2024, 1, 1)
    for i in range(1, n + 1):
        category = random.choice(CATEGORIES)
        low, high = PRICE_RANGE[category]
        rows.append([
            f"ORD-{1000 + i}",
            messy_date(start + timedelta(days=random.randint(0, 364))),
            messy_text(random.choice(CUSTOMERS)),
            messy_text(random.choice(REGIONS)),
            messy_text(category),
            random.randint(1, 8),
            messy_price(random.uniform(low, high)),
        ])

    # Inject problems
    for _ in range(4):                       # missing / placeholder values
        rows[random.randrange(n)][3] = random.choice(["", "N/A", "-"])
    for _ in range(3):
        rows[random.randrange(n)][4] = ""
    rows[10][5] = ""                         # missing quantity
    rows[20][6] = "N/A"                      # unreadable price
    rows[30][5] = -2                         # invalid quantity
    rows[40][1] = "not a date"               # unreadable date
    rows[50][0] = ""                         # missing order id
    rows.append(list(rows[5]))               # exact duplicates
    rows.append(list(rows[15]))
    rows.append(list(rows[25]))
    dup_id = list(rows[60])
    dup_id[5] = 3                            # same order id, different quantity
    rows.append(dup_id)
    random.shuffle(rows)
    return rows


def main(path="data/sample_messy_sales.csv"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([" Order ID", "Date ", "Customer", "REGION", "Product Category", "Quantity", "Unit Price"])
        writer.writerows(build_rows())
    print(f"Created {path}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
