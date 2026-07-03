from datetime import date, datetime, timedelta
from pathlib import Path
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from lib import auth, db, ui


LIME = "#C6FF3A"
LIME_DIM = "#A8B937"
INK = "#0B0B0B"
TEXT_DIM = "#B8B8B8"


def render() -> None:
    ui.render_store_badge()

    user = st.session_state.user
    store_id = user.get("store_id", "")
    if store_id == "DISTRICT":
        st.info("District Manager view — pick any store from the arena leaderboard for a "
                "deep-dive. This tab shows your primary store; DM view aggregation lands in v2.")
        return

    try:
        stores = db.read("stores")
        store = stores[stores["store_id"].astype(str) == str(store_id)].iloc[0].to_dict()
    except (IndexError, FileNotFoundError, KeyError):
        st.error(f"Couldn't load Store {store_id}.")
        return

    daily_plan = float(store.get("daily_plan", 3500))
    monthly_plan = daily_plan * 30

    submissions = _submissions_for_store(store_id)

    st.markdown("### Operations Deck")

    # ── KPI strip ────────────────────────────────────────────────────────────
    _render_kpi_strip(submissions, daily_plan, monthly_plan)

    # ── Charts ───────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        _render_traffic_chart(store_id)
    with c2:
        _render_conversion_chart(store_id)

    _render_mtd_progress(submissions, monthly_plan)

    # ── Daily manager upload for demo reporting ─────────────────────────────
    st.markdown("---")
    _render_daily_numbers_upload(store_id, daily_plan)

    # ── Weekly Targets + Monday DM Notes (leaders edit; associates read-only) ─
    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        _render_weekly_targets(store_id)
    with c4:
        _render_monday_notes(store_id)


# ── Data helpers ─────────────────────────────────────────────────────────────
def _submissions_for_store(store_id: str) -> pd.DataFrame:
    try:
        df = db.read("daily_submissions").copy()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()
    if df.empty:
        return df
    df = df[df["store_id"].astype(str) == str(store_id)]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp")


def _seed_history(store_id: str, days: int = 14) -> pd.DataFrame:
    """Deterministic synthetic history — realistic-looking traffic/conversion for the demo."""
    import hashlib
    seed = int(hashlib.md5(str(store_id).encode()).hexdigest()[:8], 16) % 1000
    rng_state = seed
    def rnd():
        nonlocal rng_state
        rng_state = (rng_state * 1103515245 + 12345) & 0x7fffffff
        return (rng_state / 0x7fffffff)

    today = date.today()
    rows = []
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        # Traffic 60-240/day, weekends higher
        base = 90 + rnd() * 100
        if d.weekday() >= 5:
            base *= 1.35
        traffic = int(base)
        # Conversion 28-42%
        conv = 0.28 + rnd() * 0.14
        trans = int(traffic * conv)
        rows.append({"date": d, "traffic": traffic, "transactions": trans,
                     "conversion": conv * 100})
    return pd.DataFrame(rows)


# ── KPI strip ────────────────────────────────────────────────────────────────
def _render_kpi_strip(subs: pd.DataFrame, daily_plan: float, monthly_plan: float) -> None:
    today_str = pd.Timestamp(date.today())
    today_subs = subs[subs["timestamp"].dt.date == today_str.date()] if not subs.empty else subs

    today_actual = float(today_subs["bold"].sum()) if not today_subs.empty else 0.0
    today_pct = (today_actual / daily_plan * 100) if daily_plan else 0
    trans = int(today_subs["trans"].sum()) if not today_subs.empty else 0
    avt = float(today_subs["avt"].mean()) if not today_subs.empty and today_subs["avt"].notna().any() else 0.0

    cards = [
        ("TODAY VS PLAN", f"{today_pct:.0f}%", f"${today_actual:,.0f} / ${daily_plan:,.0f}"),
        ("TRANSACTIONS", f"{trans}", "so far today"),
        ("AVG TICKET", f"${avt:,.0f}", "per transaction"),
        ("MTD PROJECTION", f"${today_actual * 30:,.0f}", f"pace vs ${monthly_plan:,.0f} plan"),
    ]
    cols = st.columns(len(cards))
    for col, (label, big, sub) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="glass-card" style="text-align:left;">'
                f'<div style="color:var(--text-dim);font-size:10px;letter-spacing:0.22em;font-weight:700;">{label}</div>'
                f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;'
                f'font-size:36px;color:var(--lime);line-height:1.1;">{big}</div>'
                f'<div style="color:var(--text-dim);font-size:11px;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Charts ───────────────────────────────────────────────────────────────────
def _apply_chart_theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, y=0.95,
                   font=dict(family="Instrument Serif, Georgia, serif",
                             size=22, color=LIME)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#F5F3EE"),
        margin=dict(l=10, r=10, t=50, b=30),
        height=280,
        xaxis=dict(gridcolor="rgba(245,243,238,0.06)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(245,243,238,0.06)", showline=False, zeroline=False),
        hoverlabel=dict(bgcolor="#000", font_color=LIME, bordercolor=LIME),
    )
    return fig


def _render_traffic_chart(store_id: str) -> None:
    hist = _seed_history(store_id, days=14)
    fig = go.Figure(go.Bar(
        x=hist["date"], y=hist["traffic"],
        marker=dict(color=LIME, line=dict(color=LIME_DIM, width=1)),
        hovertemplate="<b>%{x|%b %d}</b><br>%{y} visitors<extra></extra>",
    ))
    _apply_chart_theme(fig, "Traffic — last 14 days")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_conversion_chart(store_id: str) -> None:
    hist = _seed_history(store_id, days=14)
    fig = go.Figure(go.Scatter(
        x=hist["date"], y=hist["conversion"],
        mode="lines+markers",
        line=dict(color=LIME, width=3, shape="spline"),
        marker=dict(size=7, color=LIME, line=dict(color=INK, width=1)),
        fill="tozeroy",
        fillcolor="rgba(198,255,58,0.10)",
        hovertemplate="<b>%{x|%b %d}</b><br>%{y:.1f}% conv<extra></extra>",
    ))
    _apply_chart_theme(fig, "Conversion — last 14 days")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_mtd_progress(subs: pd.DataFrame, monthly_plan: float) -> None:
    # Cumulative July sales — up through today.
    if subs.empty:
        actual_by_day = pd.Series([0.0])
    else:
        month = subs[subs["timestamp"].dt.month == date.today().month]
        actual_by_day = month.groupby(month["timestamp"].dt.date)["bold"].sum().cumsum()

    # Pace line: what plan would look like if we spread linearly over 30 days.
    days_elapsed = date.today().day
    pace_target = (monthly_plan / 30) * days_elapsed
    current = float(actual_by_day.iloc[-1]) if len(actual_by_day) else 0.0

    fig = go.Figure()
    if len(actual_by_day):
        fig.add_trace(go.Scatter(
            x=list(actual_by_day.index), y=list(actual_by_day.values),
            mode="lines+markers",
            line=dict(color=LIME, width=3),
            marker=dict(size=8, color=LIME),
            fill="tozeroy", fillcolor="rgba(198,255,58,0.12)",
            name="Cumulative Sales",
        ))
    fig.add_trace(go.Scatter(
        x=[date.today() - timedelta(days=days_elapsed), date.today()],
        y=[0, monthly_plan],
        mode="lines",
        line=dict(color="#F5F3EE", width=1, dash="dot"),
        name="Plan pace",
    ))
    _apply_chart_theme(fig, f"MTD Progress · ${current:,.0f} vs ${pace_target:,.0f} pace")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Daily upload + manual numbers entry ─────────────────────────────────────
def _render_daily_numbers_upload(store_id: str, daily_plan: float) -> None:
    st.markdown("#### Daily Numbers Upload")
    if not auth.is_leader():
        _render_latest_daily_upload(store_id)
        return

    today_rows = _daily_rows_for_date(store_id, date.today())
    latest = today_rows.iloc[-1].to_dict() if not today_rows.empty else {}

    with st.container(key="daily_numbers_upload"):
        st.markdown(
            '<div class="glass-card" style="margin-bottom:12px;">'
            '<div style="color:var(--text-dim);font-size:12px;line-height:1.5;">'
            'Upload today\'s report screenshot, then enter the headline numbers. '
            'This keeps the demo accurate while the permanent spreadsheet connection is being built.'
            '</div></div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Daily report screenshot",
            type=["png", "jpg", "jpeg"],
            key=f"daily_upload_file_{store_id}",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            plan = st.number_input("Plan ($)", min_value=0.0, value=float(latest.get("plan", daily_plan) or daily_plan),
                                   step=100.0, key=f"daily_plan_{store_id}")
            bold = st.number_input("Sales / Bold ($)", min_value=0.0, value=float(latest.get("bold", 0) or 0),
                                   step=100.0, key=f"daily_bold_{store_id}")
            trans = st.number_input("Transactions", min_value=0, value=int(float(latest.get("trans", 0) or 0)),
                                    key=f"daily_trans_{store_id}")
        with c2:
            avt_default = float(latest.get("avt", 0) or 0)
            avt = st.number_input("Average Ticket ($)", min_value=0.0, value=avt_default,
                                  step=5.0, key=f"daily_avt_{store_id}")
            ep = st.number_input("Ear Piercings", min_value=0, value=int(float(latest.get("ep", 0) or 0)),
                                 key=f"daily_ep_{store_id}")
            esa = st.number_input("Warranty / ESA", min_value=0.0, value=float(latest.get("esa", 0) or 0),
                                  step=1.0, key=f"daily_esa_{store_id}")
        with c3:
            po = st.number_input("Payment Options", min_value=0, value=int(float(latest.get("po", 0) or 0)),
                                 key=f"daily_po_{store_id}")
            stj = st.number_input("St. Jude ($)", min_value=0.0, value=float(latest.get("stj", 0) or 0),
                                  step=1.0, key=f"daily_stj_{store_id}")
            computed_avt = (bold / trans) if trans else 0
            st.caption(f"Calculated AVT from sales/trans: ${computed_avt:,.0f}")

        if uploaded is not None:
            st.image(uploaded, caption="Screenshot preview", use_container_width=True)

        if st.button("Save Today's Numbers", type="primary", use_container_width=True,
                     key=f"daily_save_{store_id}"):
            screenshot_path = _save_daily_screenshot(uploaded, store_id)
            _upsert_daily_submission(
                store_id=store_id,
                submitted_by=st.session_state.user["email"],
                plan=plan,
                bold=bold,
                ep=ep,
                esa=esa,
                avt=avt or computed_avt,
                trans=trans,
                po=po,
                stj=stj,
                screenshot_path=screenshot_path or latest.get("screenshot_path", ""),
            )
            st.success("Today's numbers were saved.")
            st.rerun()


def _daily_rows_for_date(store_id: str, day: date) -> pd.DataFrame:
    try:
        df = db.read("daily_submissions").copy()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[(df["store_id"].astype(str) == str(store_id)) & (df["timestamp"].dt.date == day)]


def _save_daily_screenshot(uploaded, store_id: str) -> str:
    if uploaded is None:
        return ""
    upload_dir = Path("assets/daily_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_user = re.sub(r"[^a-z0-9]+", "_", st.session_state.user["email"].lower()).strip("_")
    ext = ".png" if uploaded.type == "image/png" else ".jpg"
    path = upload_dir / f"{date.today().isoformat()}_store_{store_id}_{safe_user}{ext}"
    path.write_bytes(uploaded.getvalue())
    return str(path)


def _upsert_daily_submission(**values) -> None:
    try:
        df = db.read("daily_submissions").copy()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame()
    now = datetime.now().replace(microsecond=0)
    if not df.empty and "timestamp" in df.columns:
        stamps = pd.to_datetime(df["timestamp"])
        window_type = df["window_type"].astype(str) if "window_type" in df.columns else pd.Series("", index=df.index)
        same_store_day = (
            (df["store_id"].astype(str) == str(values["store_id"]))
            & (stamps.dt.date == date.today())
            & (window_type == "Daily Manager Upload")
        )
        df = df[~same_store_day].copy()
    row = {
        "sub_id": f"UPLOAD_{values['store_id']}_{date.today().isoformat()}",
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "store_id": values["store_id"],
        "submitted_by": values["submitted_by"],
        "window_type": "Daily Manager Upload",
        "plan": values["plan"],
        "bold": values["bold"],
        "ep": values["ep"],
        "esa": values["esa"],
        "avt": values["avt"],
        "trans": values["trans"],
        "po": values["po"],
        "stj": values["stj"],
        "screenshot_path": values.get("screenshot_path", ""),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    db.write("daily_submissions", df)


def _render_latest_daily_upload(store_id: str) -> None:
    rows = _daily_rows_for_date(store_id, date.today())
    if rows.empty:
        st.info("No manager numbers uploaded for today yet.")
        return
    latest = rows.iloc[-1]
    st.markdown(
        f'<div class="glass-card">'
        f'<div style="color:var(--text-dim);font-size:11px;letter-spacing:0.18em;font-weight:700;">TODAY UPLOADED</div>'
        f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;font-size:28px;color:var(--lime);">'
        f'${float(latest.get("bold", 0)):,.0f}</div>'
        f'<div style="color:var(--text-dim);font-size:12px;">'
        f'{int(float(latest.get("trans", 0) or 0))} transactions · '
        f'{int(float(latest.get("ep", 0) or 0))} piercings · '
        f'${float(latest.get("stj", 0) or 0):,.0f} St. Jude</div></div>',
        unsafe_allow_html=True,
    )


# ── Editable Weekly Targets + Monday DM Notes ────────────────────────────────
def _render_weekly_targets(store_id: str) -> None:
    st.markdown("#### Weekly Targets")
    key_prefix = f"targets_{store_id}"
    if auth.is_leader():
        # Wrap in a keyed container so we can style inputs pure black + Save neon-lime.
        with st.container(key="weekly_targets_editor"):
            c1, c2 = st.columns(2)
            with c1:
                plan = st.number_input("Weekly Plan ($)", min_value=0,
                                       value=int(_load_target(store_id, "plan", 25000)),
                                       step=500, key=f"{key_prefix}_plan")
                ep = st.number_input("Ear Piercings", min_value=0,
                                     value=int(_load_target(store_id, "ep", 28)),
                                     key=f"{key_prefix}_ep")
            with c2:
                esa = st.number_input("ESA (warranties)", min_value=0,
                                      value=int(_load_target(store_id, "esa", 22)),
                                      key=f"{key_prefix}_esa")
                po = st.number_input("Payment Options", min_value=0,
                                     value=int(_load_target(store_id, "po", 12)),
                                     key=f"{key_prefix}_po")
            if st.button("Save Weekly Targets", key=f"{key_prefix}_save",
                         type="primary", use_container_width=True):
                _save_target(store_id, plan=plan, ep=ep, esa=esa, po=po)
                st.success("Weekly targets saved.")
    else:
        _render_target_readonly(store_id)


def _render_target_readonly(store_id: str) -> None:
    plan = _load_target(store_id, "plan", 25000)
    ep = _load_target(store_id, "ep", 28)
    esa = _load_target(store_id, "esa", 22)
    po = _load_target(store_id, "po", 12)
    st.markdown(
        f'<div class="glass-card">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">'
        f'<div><div style="color:var(--text-dim);font-size:10px;letter-spacing:0.2em;">WEEKLY PLAN</div>'
        f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;font-size:26px;color:var(--lime);">${int(plan):,}</div></div>'
        f'<div><div style="color:var(--text-dim);font-size:10px;letter-spacing:0.2em;">EAR PIERCINGS</div>'
        f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;font-size:26px;color:var(--lime);">{int(ep)}</div></div>'
        f'<div><div style="color:var(--text-dim);font-size:10px;letter-spacing:0.2em;">ESA</div>'
        f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;font-size:26px;color:var(--lime);">{int(esa)}</div></div>'
        f'<div><div style="color:var(--text-dim);font-size:10px;letter-spacing:0.2em;">PAYMENT OPTIONS</div>'
        f'<div style="font-family:\'Instrument Serif\',serif;font-style:italic;font-size:26px;color:var(--lime);">{int(po)}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _render_monday_notes(store_id: str) -> None:
    st.markdown("#### Monday DM Notes")
    notes_key = f"dm_notes_{store_id}"
    if auth.is_leader():
        current = _load_notes(store_id)
        text = st.text_area("Notes from the district manager for this week",
                            value=current, height=190, key=notes_key,
                            label_visibility="collapsed")
        if st.button("Save Notes", key=f"{notes_key}_save", use_container_width=True):
            _save_notes(store_id, text)
            st.success("Notes saved.")
    else:
        notes = _load_notes(store_id) or "No notes posted this week."
        st.markdown(
            f'<div class="glass-card" style="min-height:190px;white-space:pre-wrap;'
            f'font-size:14px;color:var(--text);">{notes}</div>',
            unsafe_allow_html=True,
        )


# ── Store settings persistence (small JSON sidecar) ──────────────────────────
def _settings_path() -> str:
    return "data/store_settings.json"


def _load_settings() -> dict:
    import json, os
    p = _settings_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(data: dict) -> None:
    import json
    with open(_settings_path(), "w") as f:
        json.dump(data, f, indent=2)


def _load_target(store_id: str, key: str, default: int) -> int:
    s = _load_settings()
    return int(s.get(str(store_id), {}).get("targets", {}).get(key, default))


def _save_target(store_id: str, **kwargs) -> None:
    s = _load_settings()
    s.setdefault(str(store_id), {}).setdefault("targets", {}).update(kwargs)
    _save_settings(s)


def _load_notes(store_id: str) -> str:
    s = _load_settings()
    return s.get(str(store_id), {}).get("dm_notes", "")


def _save_notes(store_id: str, text: str) -> None:
    s = _load_settings()
    s.setdefault(str(store_id), {})["dm_notes"] = text
    _save_settings(s)
