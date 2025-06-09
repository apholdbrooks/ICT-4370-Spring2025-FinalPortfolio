
#!/usr/bin/env python3
"""
Final Python Portfolio Project - Comprehensive Stock & Bond Analysis Tool
Author: Peyton Holdbrooks
Date: June 9, 2025

This script consolidates all coursework from Week 2 to Week 8:
- Basic list- and dict-based stock calculations
- OOP classes for Investment and Bond
- File I/O for stock and bond data
- SQLite database storage and queries
- JSON-based historical stock visualization
- CLI filtering enhancement
- Exception handling throughout
"""

import sqlite3
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import csv
import os

# === Utility Functions ===
def calculate_earnings(current_price, purchase_price, shares):
    return (current_price - purchase_price) * shares

def calculate_percentage_yield(current_price, purchase_price):
    return ((current_price - purchase_price) / purchase_price) * 100

def calculate_yearly_return(current_price, purchase_price, purchase_date_str):
    purchase_date = datetime.strptime(purchase_date_str, "%m/%d/%Y")
    today = datetime.today()
    years_held = (today - purchase_date).days / 365.25
    if years_held <= 0:
        return 0.0
    total_return = (current_price - purchase_price) / purchase_price
    return total_return / years_held * 100

# === OOP Classes ===
class Investor:
    def __init__(self, investor_id, name, address, phone):
        self.investor_id = investor_id
        self.name = name
        self.address = address
        self.phone = phone

class Investment:
    def __init__(self, purchase_id, symbol, quantity, purchase_price, current_price, purchase_date):
        self.purchase_id = purchase_id
        self.symbol = symbol
        self.quantity = int(quantity)
        self.purchase_price = float(purchase_price)
        self.current_price = float(current_price)
        self.purchase_date = purchase_date

    def earnings(self):
        return calculate_earnings(self.current_price, self.purchase_price, self.quantity)

    def percent_yield(self):
        return calculate_percentage_yield(self.current_price, self.purchase_price)

    def yearly_return(self):
        return calculate_yearly_return(self.current_price, self.purchase_price, self.purchase_date)

class Bond(Investment):
    def __init__(self, purchase_id, symbol, quantity, purchase_price, current_price, coupon, yield_rate, purchase_date):
        super().__init__(purchase_id, symbol, quantity, purchase_price, current_price, purchase_date)
        self.coupon = float(coupon)
        self.yield_rate = float(yield_rate.strip('%')) / 100

    def earnings(self):
        return super().earnings() + (self.quantity * self.purchase_price * self.yield_rate)

# === File I/O ===
def read_stocks(filename):
    investments = []
    try:
        with open(filename, 'r') as f:
            for idx, line in enumerate(f, start=1):
                symbol, qty, p_price, c_price, p_date = line.strip().split(',')
                investments.append(
                    Investment(f"S{idx}", symbol, qty, p_price, c_price, p_date)
                )
    except Exception as e:
        print(f"Error reading stock file '{filename}': {e}")
    return investments

def read_bonds(filename):
    bonds = []
    try:
        with open(filename, 'r') as f:
            for idx, line in enumerate(f, start=1):
                parts = line.strip().split(',')
                if len(parts) == 7:
                    symbol, qty, p_price, c_price, coupon, yld, p_date = parts
                    bonds.append(
                        Bond(f"B{idx}", symbol, qty, p_price, c_price, coupon, yld, p_date)
                    )
    except Exception as e:
        print(f"Error reading bond file '{filename}': {e}")
    return bonds

# === SQLite Database Integration ===
def setup_database(db_path, stocks, bonds):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            purchase_id TEXT PRIMARY KEY, symbol TEXT, quantity INTEGER,
            purchase_price REAL, current_price REAL, purchase_date TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonds (
            purchase_id TEXT PRIMARY KEY, symbol TEXT, quantity INTEGER,
            purchase_price REAL, current_price REAL, coupon REAL,
            yield_rate REAL, purchase_date TEXT
        );
    """)
    # Insert or replace
    for inv in stocks:
        cursor.execute("""
            INSERT OR REPLACE INTO stocks
            VALUES (?, ?, ?, ?, ?, ?)
        """, (inv.purchase_id, inv.symbol, inv.quantity,
              inv.purchase_price, inv.current_price, inv.purchase_date))
    for bond in bonds:
        cursor.execute("""
            INSERT OR REPLACE INTO bonds
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (bond.purchase_id, bond.symbol, bond.quantity,
              bond.purchase_price, bond.current_price, bond.coupon,
              bond.yield_rate, bond.purchase_date))
    conn.commit()
    return conn

# === Reporting ===
def write_report(investor, stocks, bonds, output_file):
    try:
        with open(output_file, 'w') as f:
            f.write(f"Investor: {investor.name}\n")
            f.write(f"Address: {investor.address}\n")
            f.write(f"Phone: {investor.phone}\n\n")
            f.write("STOCKS:\n")
            f.write(f"{'ID':<6}{'Symbol':<10}{'Qty':<6}{'Earn':<10}{'Yield%':<10}{'Yearly%':<10}\n")
            for s in stocks:
                f.write(f"{s.purchase_id:<6}{s.symbol:<10}{s.quantity:<6}"
                        f"{s.earnings():<10.2f}{s.percent_yield():<10.2f}{s.yearly_return():<10.2f}\n")
            f.write("\nBONDS:\n")
            f.write(f"{'ID':<6}{'Symbol':<10}{'Qty':<6}{'Earn':<10}{'Date':<12}\n")
            for b in bonds:
                f.write(f"{b.purchase_id:<6}{b.symbol:<10}{b.quantity:<6}"
                        f"{b.earnings():<10.2f}{b.purchase_date:<12}\n")
    except Exception as e:
        print(f"Failed to write report '{output_file}': {e}")

# === CSV Export ===
def export_csv(stocks, csv_file):
    try:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Symbol', 'Earnings', 'Yield%', 'Yearly%'])
            for s in stocks:
                writer.writerow([s.symbol, f"{s.earnings():.2f}", f"{s.percent_yield():.2f}", f"{s.yearly_return():.2f}"])
    except Exception as e:
        print(f"Failed to export CSV '{csv_file}': {e}")

# === CLI Filtering Enhancement ===
def interactive_portfolio_filter(stocks):
    def norm(ch): return ch.strip().lower().split()[0]
    while True:
        print("\nFilter options: [1] positive, [2] negative, [3] sort, [4] lookup, [5] exit")
        choice = norm(input("Choice: "))
        if choice in ['1','positive']:
            for s in stocks:
                if s.earnings() > 0:
                    print(f"{s.symbol}: ${s.earnings():,.2f}")
        elif choice in ['2','negative']:
            for s in stocks:
                if s.earnings() < 0:
                    print(f"{s.symbol}: ${s.earnings():,.2f}")
        elif choice in ['3','sort']:
            for s in sorted(stocks, key=lambda x: x.yearly_return(), reverse=True):
                print(f"{s.symbol}: {s.yearly_return():.2f}%")
        elif choice in ['4','lookup']:
            sym = input("Enter symbol: ").upper()
            found = [s for s in stocks if s.symbol == sym]
            if found:
                s = found[0]
                print(f"{s.symbol}: Earn={s.earnings():.2f}, Yearly%={s.yearly_return():.2f}")
            else:
                print("Not found.")
        elif choice in ['5','exit','quit']:
            break
        else:
            print("Invalid.")

# === JSON Visualization ===
def visualize_json(json_file, portfolio):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        values = defaultdict(list)
        for e in data:
            sym = e.get('Symbol')
            if sym in portfolio:
                try:
                    d = datetime.strptime(e['Date'], '%d-%b-%y')
                    val = float(e['Close']) * portfolio[sym]
                    values[sym].append((d, val))
                except:
                    continue
        plt.figure(figsize=(10,6))
        for sym, recs in values.items():
            recs.sort(key=lambda x: x[0])
            dates, vals = zip(*recs)
            plt.plot(dates, vals, label=sym)
        plt.legend(); plt.title("Portfolio Value Over Time")
        plt.savefig("portfolio_history.png")
        print("Saved portfolio_history.png")
    except Exception as e:
        print(f"Visualization failed: {e}")

# === Main ===
def main():
    investor = Investor("INV001","Peyton Holdbrooks","Denver, CO","(334)500-2140")
    stock_file = "Lesson6_Data_Stocks.txt"
    bond_file = "Week6_Data_Bonds.txt"
    db_file = "portfolio.db"
    json_file = "AllStocks.json"

    # Read files
    stocks = read_stocks(stock_file)
    bonds = read_bonds(bond_file)
    # Hardcoded bond addition
    bonds.append(Bond("B999","GT2:GOV",200,100.02,100.05,1.38,"1.35%","8/1/2017"))

    # Database
    conn = setup_database(db_file, stocks, bonds)
    # Fetch from DB if needed (not shown)
    # Reporting
    write_report(investor, stocks, bonds, "Investment_Report.txt")
    export_csv(stocks, "stock_summary.csv")

    # CLI filter
    interactive_portfolio_filter(stocks)

    # JSON viz
    portfolio_map = {s.symbol: s.quantity for s in stocks}
    visualize_json(json_file, portfolio_map)

    conn.close()

if __name__ == "__main__":
    main()
