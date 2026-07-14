"""
Chemical Solution Formulation Calculator
=========================================
A Streamlit web app that acts as a "chemical formulation engineer" and
performs accurate solution composition calculations for a 4-component
system (A, B, C, D) mixed with water at a specified molar ratio.

Run with:
    streamlit run formulation_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np

WATER_MW = 18.015       # g/mol
WATER_DENSITY = 1.000   # g/mL

st.set_page_config(page_title="Chemical Formulation Calculator", layout="wide")

st.title("🧪 Chemical Solution Formulation Calculator")
st.caption(
    "Enter compound properties, the molar mixing ratio, total solution volume "
    "and water percentage. The app calculates the full composition breakdown, "
    "concentration table, mass/volume/mole balances, and shows every formula "
    "and calculation step."
)

# -----------------------------------------------------------------------
# INPUTS
# -----------------------------------------------------------------------
st.header("1️⃣ Compound Properties & Ratio")

names = ["A", "B", "C", "D"]
default_mw = [92.09, 61.08, 105.14, 149.19]
default_density = [1.261, 1.012, 0.982, 1.038]
default_ratio = [1.0, 1.0, 1.0, 1.0]

cols = st.columns(4)
mw, density, ratio, is_amine = [], [], [], []

for i, col in enumerate(cols):
    with col:
        st.subheader(f"Compound {names[i]}")
        mw.append(
            col.number_input(
                f"MW of {names[i]} (g/mol)", min_value=0.0001,
                value=default_mw[i], step=0.01, key=f"mw_{i}",
                format="%.4f",
            )
        )
        density.append(
            col.number_input(
                f"Density of {names[i]} (g/mL)", min_value=0.0001,
                value=default_density[i], step=0.001, key=f"d_{i}",
                format="%.4f",
            )
        )
        ratio.append(
            col.number_input(
                f"Molar ratio of {names[i]}", min_value=0.0,
                value=default_ratio[i], step=0.1, key=f"r_{i}",
                format="%.4f",
            )
        )
        is_amine.append(col.checkbox(f"{names[i]} is an amine?", value=False, key=f"amine_{i}"))

st.header("2️⃣ Solution Parameters")
p1, p2 = st.columns(2)
with p1:
    total_volume = st.number_input(
        "Total solution volume (mL)", min_value=0.0001, value=1000.0, step=1.0
    )
with p2:
    water_pct = st.number_input(
        "Water percentage (%v/v of final solution)", min_value=0.0, max_value=100.0,
        value=50.0, step=0.1
    )

round_dp = st.slider("Decimal places for display", min_value=2, max_value=8, value=4)

calc_btn = st.button("🔄 Calculate", type="primary")

# -----------------------------------------------------------------------
# CALCULATION ENGINE
# -----------------------------------------------------------------------
def run_calculation(mw, density, ratio, is_amine, total_volume, water_pct):
    mw = np.array(mw, dtype=float)
    density = np.array(density, dtype=float)
    ratio = np.array(ratio, dtype=float)

    # --- Water ---
    water_volume = total_volume * (water_pct / 100.0)
    water_weight = water_volume * WATER_DENSITY
    water_moles = water_weight / WATER_MW

    # --- Remaining (non-water) volume available for A, B, C, D ---
    remaining_volume = total_volume - water_volume

    # Ratio -> volume-per-unit-n for each compound:
    # volume_i = moles_i * MW_i / density_i = (ratio_i * n) * MW_i / density_i
    vol_per_n = ratio * mw / density          # mL per unit of n, per compound
    sum_vol_per_n = vol_per_n.sum()

    if sum_vol_per_n <= 0:
        raise ValueError("Sum of ratio*MW/density is zero — check your ratio/MW/density inputs.")

    # Solve for scale factor n so that sum(volume_i) = remaining_volume
    n = remaining_volume / sum_vol_per_n

    moles = ratio * n                          # mol
    weight = moles * mw                        # g
    volume = weight / density                  # mL  (== moles * mw / density)

    total_compound_weight = weight.sum()
    total_solution_weight = total_compound_weight + water_weight
    total_compound_moles = moles.sum()
    total_all_moles = total_compound_moles + water_moles

    conc_mol_L = moles / (total_volume / 1000.0)   # mol/L, based on TOTAL solution volume
    amine_conc = conc_mol_L[np.array(is_amine, dtype=bool)].sum() if any(is_amine) else 0.0

    wt_pct = weight / total_solution_weight * 100.0
    water_wt_pct = water_weight / total_solution_weight * 100.0

    vol_pct = volume / total_volume * 100.0
    water_vol_pct = water_volume / total_volume * 100.0

    mole_fraction = moles / total_compound_moles if total_compound_moles > 0 else moles * 0
    mole_fraction_incl_water = moles / total_all_moles
    water_mole_fraction_incl_water = water_moles / total_all_moles

    sum_compound_volume = volume.sum()
    volume_balance = sum_compound_volume + water_volume
    rounding_error = volume_balance - total_volume

    return dict(
        water_volume=water_volume,
        water_weight=water_weight,
        water_moles=water_moles,
        remaining_volume=remaining_volume,
        n=n,
        moles=moles,
        weight=weight,
        volume=volume,
        total_compound_weight=total_compound_weight,
        total_solution_weight=total_solution_weight,
        total_compound_moles=total_compound_moles,
        total_all_moles=total_all_moles,
        conc_mol_L=conc_mol_L,
        amine_conc=amine_conc,
        wt_pct=wt_pct,
        water_wt_pct=water_wt_pct,
        vol_pct=vol_pct,
        water_vol_pct=water_vol_pct,
        mole_fraction=mole_fraction,
        mole_fraction_incl_water=mole_fraction_incl_water,
        water_mole_fraction_incl_water=water_mole_fraction_incl_water,
        sum_compound_volume=sum_compound_volume,
        volume_balance=volume_balance,
        rounding_error=rounding_error,
    )


# -----------------------------------------------------------------------
# DISPLAY
# -----------------------------------------------------------------------
if calc_btn:
    try:
        r = run_calculation(mw, density, ratio, is_amine, total_volume, water_pct)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    dp = round_dp

    st.header("3️⃣ Full Results Table")

    rows = []
    for i, nm in enumerate(names):
        rows.append({
            "Component": nm,
            "MW (g/mol)": round(mw[i], dp),
            "Density (g/mL)": round(density[i], dp),
            "Ratio": round(ratio[i], dp),
            "Moles (mol)": round(r["moles"][i], dp),
            "Weight (g)": round(r["weight"][i], dp),
            "Volume (mL)": round(r["volume"][i], dp),
            "Conc. (mol/L)": round(r["conc_mol_L"][i], dp),
            "wt%": round(r["wt_pct"][i], dp),
            "vol%": round(r["vol_pct"][i], dp),
            "Mole fraction (of compounds)": round(r["mole_fraction"][i], dp),
            "Mole fraction (incl. water)": round(r["mole_fraction_incl_water"][i], dp),
            "Amine?": "Yes" if is_amine[i] else "No",
        })

    rows.append({
        "Component": "Water",
        "MW (g/mol)": round(WATER_MW, dp),
        "Density (g/mL)": round(WATER_DENSITY, dp),
        "Ratio": "-",
        "Moles (mol)": round(r["water_moles"], dp),
        "Weight (g)": round(r["water_weight"], dp),
        "Volume (mL)": round(r["water_volume"], dp),
        "Conc. (mol/L)": "-",
        "wt%": round(r["water_wt_pct"], dp),
        "vol%": round(r["water_vol_pct"], dp),
        "Mole fraction (of compounds)": "-",
        "Mole fraction (incl. water)": round(r["water_mole_fraction_incl_water"], dp),
        "Amine?": "-",
    })

    df_full = pd.DataFrame(rows)
    st.dataframe(df_full, use_container_width=True, hide_index=True)

    st.subheader("Totals & Balance Checks")
    t1, t2, t3 = st.columns(3)
    t1.metric("Total solution weight (g)", f"{r['total_solution_weight']:.{dp}f}")
    t2.metric("Total compound moles (mol)", f"{r['total_compound_moles']:.{dp}f}")
    t3.metric("Total moles incl. water (mol)", f"{r['total_all_moles']:.{dp}f}")

    if any(is_amine):
        st.metric("Total amine concentration (mol/L)", f"{r['amine_conc']:.{dp}f}")
    else:
        st.info("No compound flagged as an amine — total amine concentration not applicable.")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Sum of compound volumes (mL)", f"{r['sum_compound_volume']:.{dp}f}")
    b2.metric("Water volume (mL)", f"{r['water_volume']:.{dp}f}")
    b3.metric("Volume balance (mL)", f"{r['volume_balance']:.{dp}f}")
    b4.metric("Target total volume (mL)", f"{total_volume:.{dp}f}")

    if abs(r["rounding_error"]) < 1e-9:
        st.success("✅ Volume balance check passed exactly: Σ(compound volumes) + water volume = total volume.")
    else:
        st.warning(
            f"⚠️ Rounding/consistency error = {r['rounding_error']:.{dp}f} mL "
            f"(volume balance − target total volume). This is expected due to "
            f"floating-point/display rounding at {dp} decimal places; the underlying "
            f"unrounded calculation is exact by construction (the scale factor n is "
            f"solved so that Σ volume_i = remaining_volume)."
        )

    # -------------------------------------------------------------
    st.header("4️⃣ Summary Table")
    summary_rows = []
    for i, nm in enumerate(names):
        summary_rows.append({
            "Compound": nm,
            "Molecular Weight (g/mol)": round(mw[i], dp),
            "Density (g/mL)": round(density[i], dp),
            "Moles": round(r["moles"][i], dp),
            "Weight (g)": round(r["weight"][i], dp),
            "Volume (mL)": round(r["volume"][i], dp),
        })
    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    csv = df_summary.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download summary table (CSV)", csv, "formulation_summary.csv", "text/csv")

    csv_full = df_full.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download full results table (CSV)", csv_full, "formulation_full_results.csv", "text/csv")

    # -------------------------------------------------------------
    st.header("5️⃣ Formulas Used")
    st.markdown(r"""
| # | Quantity | Formula |
|---|----------|---------|
| 1 | Water volume | $V_{water} = V_{total} \times \dfrac{\%water}{100}$ |
| 2 | Water weight | $W_{water} = V_{water} \times \rho_{water}$ |
| 3 | Remaining (non-water) volume | $V_{remaining} = V_{total} - V_{water}$ |
| 4 | Volume of compound $i$ per unit scale factor | $v_i = ratio_i \times \dfrac{MW_i}{\rho_i}$ |
| 5 | Scale factor (solved from mass/volume balance) | $n = \dfrac{V_{remaining}}{\sum v_i}$ |
| 6 | Moles of compound $i$ | $mol_i = ratio_i \times n$ |
| 7 | Weight of compound $i$ | $W_i = mol_i \times MW_i$ |
| 8 | Volume of compound $i$ | $V_i = \dfrac{W_i}{\rho_i}$ |
| 9 | Total solution weight | $W_{total} = W_{water} + \sum W_i$ |
| 10 | Total compound moles | $mol_{total} = \sum mol_i$ |
| 11 | Concentration of compound $i$ | $C_i \ (mol/L) = \dfrac{mol_i}{V_{total}\ (L)}$ |
| 12 | Total amine concentration | $C_{amine} = \sum C_i$ for all $i$ flagged as amine |
| 13 | Weight percent of compound $i$ | $wt\%_i = \dfrac{W_i}{W_{total}} \times 100$ |
| 14 | Volume percent of compound $i$ | $vol\%_i = \dfrac{V_i}{V_{total}} \times 100$ |
| 15 | Mole fraction (compounds only) | $x_i = \dfrac{mol_i}{\sum_j mol_j}$ |
| 16 | Mole fraction (incl. water) | $x_i = \dfrac{mol_i}{mol_{total} + mol_{water}}$ |
| 17 | Balance check | $\sum V_i + V_{water} \overset{?}{=} V_{total}$ |
""")

    st.header("6️⃣ Step-by-Step Calculation Log")
    log = []
    log.append(f"INPUTS")
    log.append(f"  Total solution volume, V_total = {total_volume} mL")
    log.append(f"  Water percentage = {water_pct} %")
    for i, nm in enumerate(names):
        log.append(f"  {nm}: MW = {mw[i]} g/mol, density = {density[i]} g/mL, ratio = {ratio[i]}, amine = {is_amine[i]}")

    log.append("")
    log.append("STEP 1 — Water volume")
    log.append(f"  V_water = V_total * (water% / 100) = {total_volume} * ({water_pct} / 100) = {r['water_volume']:.{dp}f} mL")

    log.append("")
    log.append("STEP 2 — Water weight")
    log.append(f"  W_water = V_water * density_water = {r['water_volume']:.{dp}f} * {WATER_DENSITY} = {r['water_weight']:.{dp}f} g")

    log.append("")
    log.append("STEP 3 — Remaining (non-water) volume")
    log.append(f"  V_remaining = V_total - V_water = {total_volume} - {r['water_volume']:.{dp}f} = {r['remaining_volume']:.{dp}f} mL")

    log.append("")
    log.append("STEP 4 — Volume-per-unit-n for each compound (v_i = ratio_i * MW_i / density_i)")
    for i, nm in enumerate(names):
        v_i = ratio[i] * mw[i] / density[i]
        log.append(f"  v_{nm} = {ratio[i]} * {mw[i]} / {density[i]} = {v_i:.{dp}f} mL per unit n")

    sum_vpn = sum(ratio[i] * mw[i] / density[i] for i in range(4))
    log.append(f"  Sum(v_i) = {sum_vpn:.{dp}f} mL per unit n")

    log.append("")
    log.append("STEP 5 — Solve scale factor n")
    log.append(f"  n = V_remaining / Sum(v_i) = {r['remaining_volume']:.{dp}f} / {sum_vpn:.{dp}f} = {r['n']:.{dp}f}")

    log.append("")
    log.append("STEP 6 — Moles of each compound (moles_i = ratio_i * n)")
    for i, nm in enumerate(names):
        log.append(f"  mol_{nm} = {ratio[i]} * {r['n']:.{dp}f} = {r['moles'][i]:.{dp}f} mol")

    log.append("")
    log.append("STEP 7 — Weight of each compound (W_i = mol_i * MW_i)")
    for i, nm in enumerate(names):
        log.append(f"  W_{nm} = {r['moles'][i]:.{dp}f} * {mw[i]} = {r['weight'][i]:.{dp}f} g")

    log.append("")
    log.append("STEP 8 — Volume of each compound (V_i = W_i / density_i)")
    for i, nm in enumerate(names):
        log.append(f"  V_{nm} = {r['weight'][i]:.{dp}f} / {density[i]} = {r['volume'][i]:.{dp}f} mL")

    log.append("")
    log.append("STEP 9 — Total solution weight")
    log.append(f"  W_total = W_water + Sum(W_i) = {r['water_weight']:.{dp}f} + {r['total_compound_weight']:.{dp}f} = {r['total_solution_weight']:.{dp}f} g")

    log.append("")
    log.append("STEP 10 — Total moles of compounds")
    log.append(f"  mol_total(compounds) = Sum(mol_i) = {r['total_compound_moles']:.{dp}f} mol")
    log.append(f"  mol_water = W_water / MW_water = {r['water_weight']:.{dp}f} / {WATER_MW} = {r['water_moles']:.{dp}f} mol")
    log.append(f"  mol_total(incl. water) = {r['total_all_moles']:.{dp}f} mol")

    log.append("")
    log.append("STEP 11 — Concentration (mol/L) of each compound (based on total solution volume)")
    for i, nm in enumerate(names):
        log.append(f"  C_{nm} = mol_{nm} / (V_total / 1000) = {r['moles'][i]:.{dp}f} / ({total_volume}/1000) = {r['conc_mol_L'][i]:.{dp}f} mol/L")

    log.append("")
    log.append("STEP 12 — Total amine concentration")
    if any(is_amine):
        amine_names = [names[i] for i in range(4) if is_amine[i]]
        log.append(f"  Amine-flagged compounds: {', '.join(amine_names)}")
        log.append(f"  C_amine = Sum(C_i for amine i) = {r['amine_conc']:.{dp}f} mol/L")
    else:
        log.append("  No compound flagged as amine -> not applicable")

    log.append("")
    log.append("STEP 13 — Weight percent")
    for i, nm in enumerate(names):
        log.append(f"  wt%_{nm} = W_{nm}/W_total * 100 = {r['weight'][i]:.{dp}f}/{r['total_solution_weight']:.{dp}f} * 100 = {r['wt_pct'][i]:.{dp}f} %")
    log.append(f"  wt%_water = {r['water_weight']:.{dp}f}/{r['total_solution_weight']:.{dp}f} * 100 = {r['water_wt_pct']:.{dp}f} %")

    log.append("")
    log.append("STEP 14 — Volume percent")
    for i, nm in enumerate(names):
        log.append(f"  vol%_{nm} = V_{nm}/V_total * 100 = {r['volume'][i]:.{dp}f}/{total_volume} * 100 = {r['vol_pct'][i]:.{dp}f} %")
    log.append(f"  vol%_water = {r['water_volume']:.{dp}f}/{total_volume} * 100 = {r['water_vol_pct']:.{dp}f} %")

    log.append("")
    log.append("STEP 15 — Mole fraction (compounds only)")
    for i, nm in enumerate(names):
        log.append(f"  x_{nm} = mol_{nm}/mol_total(compounds) = {r['moles'][i]:.{dp}f}/{r['total_compound_moles']:.{dp}f} = {r['mole_fraction'][i]:.{dp}f}")

    log.append("")
    log.append("STEP 16 — Balance check")
    log.append(f"  Sum(V_i) + V_water = {r['sum_compound_volume']:.{dp}f} + {r['water_volume']:.{dp}f} = {r['volume_balance']:.{dp}f} mL")
    log.append(f"  Target V_total = {total_volume} mL")
    log.append(f"  Rounding error = {r['rounding_error']:.{dp}f} mL")

    st.code("\n".join(log), language="text")

else:
    st.info("Fill in the parameters above and click **Calculate** to run the formulation engine.")

st.markdown("---")
st.caption(
    "Notes: (1) The scale factor n is solved analytically so that the sum of compound "
    "volumes plus water volume equals the target total solution volume exactly (up to "
    "floating point precision) — this is the key equation linking the molar ratio to real "
    "volumes. (2) Concentration (mol/L) is computed relative to the FINAL total solution "
    "volume, which is standard practice for reporting solution molarity. (3) Mole fraction "
    "is reported both among the four compounds only, and including water, since either "
    "convention may be relevant depending on context."
)