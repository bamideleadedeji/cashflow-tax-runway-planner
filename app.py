"""
13-Week Cash-Flow Runway, Burn-Rate & Quarterly Tax Reserve Planner (v2.0)
Interactive Treasury Dashboard, Profit-First Tax Reserve Calculator & Multi-Sheet Excel Export
"""

import io
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import plotly.express as px
from cashflow_engine import DEFAULT_13_WEEKS, build_13week_forecast

st.set_page_config(page_title="13-Week Cash-Flow & Tax Reserve Planner", page_icon="💵", layout="wide")
st.title("💵 13-Week Cash-Flow Runway, Burn-Rate & Quarterly Tax Reserve Planner")
st.caption("Rolling 13-Week Treasury Forecast • Profit-First Quarterly Tax Set-Aside • True Spendable Cash vs. Bank Balance • Stress Scenarios")
st.divider()

starting_cash = st.sidebar.number_input("Starting Bank Cash Balance ($ USD)", min_value=0.0, max_value=10000000.0, value=42500.0, step=1000.0)
tax_rate_pct = st.sidebar.slider("Quarterly Tax Reserve Rate (% of Net Profit)", min_value=0.0, max_value=45.0, value=25.0, step=1.0)
min_buffer_usd = st.sidebar.number_input("Minimum Cash Safety Buffer ($ USD)", min_value=0.0, max_value=5000000.0, value=15000.0, step=1000.0)
stress_rev_drop = st.sidebar.slider("Stress Test: Revenue Drop Scenario (%)", min_value=0, max_value=50, value=20, step=5)

uploaded = st.sidebar.file_uploader("Upload Custom 13-Week Cash Ledger (.csv or .xlsx)", type=["csv", "xlsx"])
base_df = (pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)) if uploaded else pd.DataFrame(DEFAULT_13_WEEKS)

st.subheader("Interactive 13-Week Cash Inflows & Operating Outflows Schedule")
st.caption("Edit any weekly inflow or expense cell below to recalculate cash runway and quarterly tax reserves instantaneously.")
edited_df = st.data_editor(base_df, width="stretch", num_rows="dynamic")

res = build_13week_forecast(edited_df, starting_cash=starting_cash, tax_rate_pct=tax_rate_pct, min_buffer_usd=min_buffer_usd)

stress_df = edited_df.copy()
stress_df["Expected_Inflows_USD"] = stress_df["Expected_Inflows_USD"] * (1.0 - stress_rev_drop / 100.0)
stress_res = build_13week_forecast(stress_df, starting_cash=starting_cash, tax_rate_pct=tax_rate_pct, min_buffer_usd=min_buffer_usd)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Week 13 Bank Balance", f"${res['ending_bank_cash']:,.2f}", delta=f"Net 13W Change: ${res['ending_bank_cash'] - starting_cash:,.2f}")
c2.metric("Accrued Tax Reserve (13W)", f"${res['total_tax_reserve']:,.2f}", delta=f"{tax_rate_pct:.0f}% Set-Aside Rate")
c3.metric("True Spendable Cash (W13)", f"${res['ending_spendable_cash']:,.2f}", delta="Bank Cash Minus Tax Liability")
c4.metric("Gross Cash Runway", f"{res['runway_weeks']:.1f} Weeks", delta=f"Avg Weekly Burn: ${res['avg_weekly_burn']:,.2f}")

if res["breach_week"]:
    st.warning(f"⚠️ Liquidity Alert: True Spendable Cash dips below your ${min_buffer_usd:,.2f} safety buffer in **{res['breach_week']}**.")
else:
    st.success(f"✅ Healthy Liquidity: True Spendable Cash stays above your ${min_buffer_usd:,.2f} safety buffer across all 13 weeks!")

tab1, tab2, tab3 = st.tabs(["📈 Cash Runway & Tax Reserve Chart", "📋 Full 13-Week Treasury Ledger", "📥 Excel Treasury Workbook & Stress Export"])

with tab1:
    st.plotly_chart(px.line(res["forecast_df"], x="Week", y=["Ending_Bank_Cash_USD", "True_Spendable_Cash_USD"], markers=True, title="13-Week Ending Bank Balance vs. True Spendable Cash ($)"), width="stretch")

with tab2:
    st.dataframe(res["forecast_df"], width="stretch")
    st.info(f"Stress Test (-{stress_rev_drop}% Revenue Dip): Week 13 Spendable Cash drops to **${stress_res['ending_spendable_cash']:,.2f}** (Breach Week: {stress_res['breach_week'] or 'None'}).")

with tab3:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame([
            {"Treasury_Metric": "Report Generated (UTC)", "Value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")},
            {"Treasury_Metric": "Starting Bank Cash ($)", "Value": f"${starting_cash:,.2f}"},
            {"Treasury_Metric": "13-Week Total Inflows ($)", "Value": f"${res['total_inflows']:,.2f}"},
            {"Treasury_Metric": "13-Week Total Outflows ($)", "Value": f"${res['total_outflows']:,.2f}"},
            {"Treasury_Metric": "Week 13 Ending Bank Cash ($)", "Value": f"${res['ending_bank_cash']:,.2f}"},
            {"Treasury_Metric": "Quarterly Tax Reserve Set-Aside ($)", "Value": f"${res['total_tax_reserve']:,.2f}"},
            {"Treasury_Metric": "Week 13 True Spendable Cash ($)", "Value": f"${res['ending_spendable_cash']:,.2f}"},
            {"Treasury_Metric": "Stress Test (-20% Rev) Spendable Cash ($)", "Value": f"${stress_res['ending_spendable_cash']:,.2f}"},
        ]).to_excel(writer, sheet_name="01_Executive_Cash_Summary", index=False)
        res["forecast_df"].to_excel(writer, sheet_name="02_13Week_Cash_Forecast", index=False)
        stress_res["forecast_df"].to_excel(writer, sheet_name="03_Revenue_Drop_Stress_Test", index=False)

    memo = (
        f"13-WEEK TREASURY RUNWAY & TAX RESERVE BRIEFING\n"
        f"Generated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"------------------------------------------------------------\n"
        f"1. Starting Cash         : ${starting_cash:,.2f}\n"
        f"2. Week 13 Bank Balance  : ${res['ending_bank_cash']:,.2f}\n"
        f"3. Tax Reserve Liability : ${res['total_tax_reserve']:,.2f} ({tax_rate_pct:.0f}% rate)\n"
        f"4. True Spendable Cash   : ${res['ending_spendable_cash']:,.2f}\n"
        f"5. Gross Runway          : {res['runway_weeks']:.1f} weeks (Avg Burn: ${res['avg_weekly_burn']:,.2f}/wk)\n"
    )
    d1, d2 = st.columns(2)
    d1.download_button("📊 Download 3-Sheet Excel Cash & Tax Workbook (.xlsx)", buf.getvalue(), "13Week_CashFlow_Tax_Planner.xlsx")
    d2.download_button("📄 Download Founder Cash & Tax Briefing (.txt)", memo, "13Week_CashFlow_Briefing.txt")
