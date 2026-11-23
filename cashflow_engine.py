"""
13-Week Cash-Flow Runway, Burn-Rate & Quarterly Tax Reserve Engine
Models rolling 13-week liquidity, net burn, tax set-aside liabilities, and stress scenarios.
"""

import pandas as pd

DEFAULT_13_WEEKS = [
    {"Week": f"Week {i:02d}", "Expected_Inflows_USD": 14500 if i % 2 == 1 else 11200, "Payroll_And_Contractors_USD": 6800 if i % 2 == 0 else 1200, "Fixed_Ops_And_SaaS_USD": 2400, "Variable_COGS_And_Ads_USD": 2900}
    for i in range(1, 14)
]


def build_13week_forecast(df: pd.DataFrame, starting_cash: float, tax_rate_pct: float, min_buffer_usd: float) -> dict:
    """Computes rolling 13-week cash runway, spendable cash net of tax reserves, and liquidity alerts."""
    work = df.copy()
    cash = float(starting_cash)
    tax_rate = float(tax_rate_pct) / 100.0
    accrued_tax = 0.0

    ending_cash_list = []
    net_flow_list = []
    tax_setaside_list = []
    spendable_cash_list = []
    status_list = []
    runway_breach_week = None

    for _, row in work.iterrows():
        inflow = float(row.get("Expected_Inflows_USD", 0.0))
        outflow = (
            float(row.get("Payroll_And_Contractors_USD", 0.0))
            + float(row.get("Fixed_Ops_And_SaaS_USD", 0.0))
            + float(row.get("Variable_COGS_And_Ads_USD", 0.0))
        )
        net_flow = round(inflow - outflow, 2)
        weekly_tax = round(max(0.0, net_flow) * tax_rate, 2)
        accrued_tax = round(accrued_tax + weekly_tax, 2)
        cash = round(cash + net_flow, 2)
        spendable = round(cash - accrued_tax, 2)

        if spendable < min_buffer_usd and runway_breach_week is None:
            runway_breach_week = str(row.get("Week", "Unknown"))

        if spendable < 0:
            st_flag = "CRITICAL DEFICIT"
        elif spendable < min_buffer_usd:
            st_flag = "BELOW SAFETY BUFFER"
        else:
            st_flag = "HEALTHY LIQUIDITY"

        net_flow_list.append(net_flow)
        tax_setaside_list.append(weekly_tax)
        ending_cash_list.append(cash)
        spendable_cash_list.append(spendable)
        status_list.append(st_flag)

    work["Net_Weekly_CashFlow_USD"] = net_flow_list
    work["Tax_Reserve_Transfer_USD"] = tax_setaside_list
    work["Ending_Bank_Cash_USD"] = ending_cash_list
    work["True_Spendable_Cash_USD"] = spendable_cash_list
    work["Liquidity_Status"] = status_list

    total_inflows = round(float(work["Expected_Inflows_USD"].sum()), 2)
    total_outflows = round(float((work["Payroll_And_Contractors_USD"] + work["Fixed_Ops_And_SaaS_USD"] + work["Variable_COGS_And_Ads_USD"]).sum()), 2)
    avg_weekly_burn = round(total_outflows / max(len(work), 1), 2)
    runway_weeks = round(starting_cash / avg_weekly_burn, 1) if avg_weekly_burn > 0 else 99.9

    return {
        "forecast_df": work,
        "ending_bank_cash": ending_cash_list[-1] if ending_cash_list else starting_cash,
        "total_tax_reserve": accrued_tax,
        "ending_spendable_cash": spendable_cash_list[-1] if spendable_cash_list else starting_cash,
        "total_inflows": total_inflows,
        "total_outflows": total_outflows,
        "avg_weekly_burn": avg_weekly_burn,
        "runway_weeks": runway_weeks,
        "breach_week": runway_breach_week,
    }
