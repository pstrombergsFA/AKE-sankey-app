import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# -----------------------
# HARDCODED LOGIN
# -----------------------
VALID_USERNAME = "SFS"
VALID_PASSWORD = "SFS1"

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Logged in successfully")
        else:
            st.error("Invalid username or password")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv(CSV_URL)

# normalize columns just in case
df.columns = df.columns.str.strip().str.lower()

# -----------------------
# UI CONTROLS
# -----------------------
month = st.selectbox("Select month", sorted(df["month"].unique()))
year = st.selectbox("Select year", sorted(df["year"].unique()))

df_filtered = df[(df["month"] == month) & (df["year"] == year)]

# -----------------------
# SANKEY LOGIC
# -----------------------
# Clean columns
df.columns = df.columns.str.strip().str.lower()
df["value"] = df["value"].astype(float)

# Create name mapping (mapping -> name)
name_map = df[["mapping", "name"]].drop_duplicates().set_index("mapping")["name"].to_dict()

# Get unique values dynamically
years = sorted(df["year"].unique())
months = sorted(df["month"].unique())
quarters = sorted(df["quarter"].unique())

# Build all (year, period_type, period_val) combos
# Grouped by year for the dropdown: Year buttons on top,
# under each year all months then quarters
combos = []
for y in years:
    for m in months:
        combos.append((y, "Month", m))
    for q in quarters:
        combos.append((y, "Quarter", q))

# Color based on value
def get_node_color(value):
    return "#4CAF50" if value >= 0 else "#F44336"

# -----------------------
# Build all Sankey traces (one per combo)
# -----------------------
fig = go.Figure()

for trace_idx, (year, period_type, period_val) in enumerate(combos):

    # Filter
    mask = df["year"] == year
    if period_type == "Month":
        mask &= df["month"] == period_val
        period_label = f"Month {period_val}"
    else:
        mask &= df["quarter"] == period_val
        period_label = f"Q{period_val}"

    mdf = df[mask].copy()

    # Categorise dynamically
    revenues, gp_items, cost_items = {}, {}, {}
    ebitda_val = 0

    for mapping in mdf["mapping"].unique():
        val = mdf.loc[mdf["mapping"] == mapping, "value"].sum()
        if val == 0:
            continue
        if mapping == "EBITDA":
            ebitda_val = val
        elif mapping.startswith("GP_"):
            gp_items[mapping] = val
        elif mapping.startswith("T_"):
            cost_items[mapping] = val
        else:
            revenues[mapping] = val

    # Sort alphabetically
    revenues   = dict(sorted(revenues.items()))
    gp_items   = dict(sorted(gp_items.items()))
    cost_items = dict(sorted(cost_items.items()))

    # Totals
    total_revenue  = sum(revenues.values())
    total_gp       = sum(gp_items.values())
    total_costs    = sum(cost_items.values())
    total_op_costs = abs(total_costs)

    # ====== LABELS & COLORS ======
    labels, node_colors = [], []

    labels.append(f"Total Revenue<br>{total_revenue:,.0f}")
    node_colors.append(get_node_color(total_revenue))

    for r, v in revenues.items():
        pct = (v / total_revenue * 100) if total_revenue != 0 else 0
        labels.append(f"{name_map.get(r, r)}<br>{v:,.0f} ({pct:.1f}%)")
        node_colors.append(get_node_color(v))

    labels.append("")                   # slim connector
    node_colors.append("#CCCCCC")

    for gp, v in gp_items.items():
        pct = (v / total_revenue * 100) if total_revenue != 0 else 0
        labels.append(f"{name_map.get(gp, gp)}<br>{v:,.0f} ({pct:.1f}%)")
        node_colors.append(get_node_color(v))

    labels.append(f"Gross Profit<br>{total_gp:,.0f}")
    node_colors.append(get_node_color(total_gp))

    for cost, v in cost_items.items():
        pct = (abs(v) / total_op_costs * 100) if total_op_costs != 0 else 0
        labels.append(f"{name_map.get(cost, cost)}<br>{v:,.0f} ({pct:.1f}%)")
        node_colors.append(get_node_color(v))

    labels.append(f"Operational Costs<br>{total_costs:,.0f}")
    node_colors.append(get_node_color(total_costs))

    labels.append(f"EBITDA<br>{ebitda_val:,.0f}")
    node_colors.append(get_node_color(ebitda_val))

    # ====== INDEX MAP ======
    idx, pos = {}, 0
    idx["Total Revenue"]    = pos; pos += 1
    for r in revenues:       idx[r] = pos; pos += 1
    idx["Connector"]        = pos; pos += 1
    for gp in gp_items:      idx[gp] = pos; pos += 1
    idx["Gross Profit"]     = pos; pos += 1
    for cost in cost_items:  idx[cost] = pos; pos += 1
    idx["Operational Costs"]= pos; pos += 1
    idx["EBITDA"]           = pos

    # ====== LINKS ======
    source, target, value = [], [], []

    for r, v in revenues.items():
        source.append(idx["Total Revenue"]); target.append(idx[r]);           value.append(abs(v))
    for r, v in revenues.items():
        source.append(idx[r]);              target.append(idx["Connector"]);  value.append(abs(v))
    for gp, v in gp_items.items():
        source.append(idx["Connector"]);    target.append(idx[gp]);           value.append(abs(v))
    for gp, v in gp_items.items():
        source.append(idx[gp]);             target.append(idx["Gross Profit"]); value.append(abs(v))
    for cost, v in cost_items.items():
        source.append(idx["Gross Profit"]); target.append(idx[cost]);         value.append(abs(v))
    for cost, v in cost_items.items():
        source.append(idx[cost]);           target.append(idx["Operational Costs"]); value.append(abs(v))

    if ebitda_val >= 0:
        source.append(idx["Gross Profit"]);      target.append(idx["EBITDA"]);            value.append(abs(ebitda_val))
    else:
        source.append(idx["EBITDA"]);            target.append(idx["Operational Costs"]); value.append(abs(ebitda_val))

    # ====== TRACE ======
    node_thickness = [20] * len(labels)
    node_thickness[idx["Connector"]] = 2

    fig.add_trace(
        go.Sankey(
            visible=(trace_idx == 0),
            arrangement="snap",
            node=dict(
                label=labels,
                pad=15,
                color=node_colors,
                line=dict(color="black", width=0.5)
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color="rgba(180,180,180,0.3)"
            )
        )
    )

# -----------------------
# Two dropdowns: Year  &  Period
# Each button stores the FULL visibility vector so both dropdowns
# work independently without resetting each other.
# -----------------------

# Pre-compute index of the "current" combo for every (year, period_type, period_val)
combo_index = {c: i for i, c in enumerate(combos)}
total_traces = len(combos)

# --- helper ---
def vis(year, period_type, period_val):
    """Return visibility list with only the matching trace shown."""
    target = combo_index.get((year, period_type, period_val), 0)
    return [i == target for i in range(total_traces)]

# ---- Year dropdown ----
# Clicking a year keeps the period that is currently shown.
# Plotly menus can't read each other's state, so we use a workaround:
# each year button shows Month 1 of that year (sensible default).
# We add a second menu for Period that shows the chosen period for
# the *first* year — Plotly will execute both arg-sets if we nest them
# as a single combined menu instead.
#
# BEST APPROACH for Plotly: a single dropdown with clearly grouped labels.

buttons = []
for y in years:
    # Year header (disabled-style: just a label line)
    buttons.append(dict(
        label=f"─── {y} ───",
        method="update",
        args=[
            {"visible": vis(y, "Month", months[0])},
            {"title": f"Income Statement – {y} – Month {months[0]}"}
        ]
    ))
    for m in months:
        buttons.append(dict(
            label=f"  Month {m}",
            method="update",
            args=[
                {"visible": vis(y, "Month", m)},
                {"title": f"Income Statement – {y} – Month {m}"}
            ]
        ))
    for q in quarters:
        buttons.append(dict(
            label=f"  Q{q}",
            method="update",
            args=[
                {"visible": vis(y, "Quarter", q)},
                {"title": f"Income Statement – {y} – Q{q}"}
            ]
        ))

fig.update_layout(
    updatemenus=[
        dict(
            buttons=buttons,
            direction="down",
            x=0.01,
            y=1.15,
            xanchor="left",
            yanchor="top"
        )
    ],
    annotations=[
        dict(text="Year / Period", x=0.01, xref="paper", y=1.21, yref="paper",
             showarrow=False, font=dict(size=11, color="#444"))
    ],
    title=f"Income Statement – {years[0]} – Month {months[0]}",
    height=900,
    font=dict(size=10)
)

fig.show()

st.plotly_chart(fig, use_container_width=True)
