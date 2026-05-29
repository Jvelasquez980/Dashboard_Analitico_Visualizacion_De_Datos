import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="NYC 311 — SLA Cost Intelligence",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DARK   = "#0d1117"
PANEL  = "#161b22"
PANEL2 = "#1c2333"
BORDER = "#30363d"
ACCENT = "#f97316"
WHITE  = "#f8fafc"
GRAY   = "#94a3b8"
GRAY2  = "#64748b"
RED    = "#ef4444"
GREEN  = "#22c55e"
YELLOW = "#eab308"
BLUE   = "#3b82f6"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  html, body, [class*="css"] {{
    background-color:{DARK}; color:{WHITE}; font-family:'Inter',sans-serif;
  }}
  .block-container {{ padding:1.5rem 2.5rem 3rem; max-width:1400px; }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
    background-color:{PANEL}; border-right:1px solid {BORDER};
  }}
  section[data-testid="stSidebar"] .block-container {{ padding: 1.5rem 1rem; }}

  /* ── Widget labels ── */
  .stSelectbox label, .stMultiSelect label, .stSlider label {{
    color:{GRAY}!important; font-size:0.72rem;
    text-transform:uppercase; letter-spacing:0.08em; font-weight:600;
  }}

  /* ── KPI cards ── */
  .kpi-card {{
    background:{PANEL};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:1.1rem 1.3rem;
    text-align:center;
    transition: border-color 0.2s;
    height: 100%;
  }}
  .kpi-card:hover {{ border-color: {ACCENT}44; }}

  /* ── Section headers ── */
  .section-header {{
    font-size:0.68rem; text-transform:uppercase; letter-spacing:0.12em;
    color:{GRAY2}; margin-bottom:0.5rem; padding-bottom:0.4rem;
    border-bottom:1px solid {BORDER}; font-weight:600;
  }}

  /* ── Story label above chart ── */
  .story-label {{
    font-size:0.82rem; color:{WHITE}; font-weight:600;
    margin-bottom:0.15rem;
  }}
  .story-sub {{
    font-size:0.72rem; color:{GRAY}; margin-bottom:0.6rem;
  }}

  /* ── Finding box ── */
  .finding-box {{
    background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
    border-left:4px solid {ACCENT};
    border-radius:0 10px 10px 0;
    padding:1rem 1.5rem;
    margin:0.6rem 0;
  }}

  /* ── Hypothesis box ── */
  .hypothesis-box {{
    background:linear-gradient(135deg,#1a1f2e 0%,#0f1420 100%);
    border:1px solid {ACCENT}55;
    border-radius:12px;
    padding:1.2rem 1.5rem;
    margin:0.6rem 0;
  }}

  /* ── Divider with label ── */
  .section-divider {{
    display:flex; align-items:center; gap:0.75rem; margin:1.5rem 0 1rem;
  }}
  .section-divider-line {{
    flex:1; height:1px; background:{BORDER};
  }}
  .section-divider-label {{
    font-size:0.65rem; text-transform:uppercase; letter-spacing:0.15em;
    color:{GRAY2}; font-weight:700; white-space:nowrap;
  }}

  /* ── Stat pill ── */
  .stat-pill {{
    display:inline-block; background:{PANEL2};
    border:1px solid {BORDER}; border-radius:20px;
    padding:0.2rem 0.75rem; font-size:0.72rem; color:{GRAY};
    margin-right:0.4rem; margin-top:0.3rem;
  }}

  h1,h2,h3 {{ color:{WHITE}!important; }}

  [data-testid="stFileUploadDropzone"] {{
    background:{PANEL}!important; border:2px dashed {BORDER}!important;
    border-radius:10px!important;
  }}

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {{ border-radius:10px; overflow:hidden; }}

  /* ── Streamlit hr ── */
  hr {{ border-color:{BORDER}!important; margin: 1rem 0!important; }}
</style>
""", unsafe_allow_html=True)

# ─── BUSINESS MAPPING ───
BUSINESS_MAPPING = {
    "DOT":   (5.0,   83448.0),
    "NYPD":  (0.33,  64277.0),
    "DSNY":  (2.0,   79301.0),
    "DPR":   (8.0,   68022.0),
    "DOB":   (40.0, 106907.0),
    "DEP":   (0.25,  75757.0),
    "HPD":   (12.0, 252387.0),
    "DOE":   (10.0, 119316.0),
    "DHS":   (0.17,  41500.0),
    "DOHMH": (14.0,  74717.0),
    "TLC":   (14.0,  74717.0),
    "DCA":   (22.0,  74717.0),
    "DOITT": (3.0,   74717.0),
    "EDC":   (10.0,  74717.0),
}

@st.cache_data(show_spinner="Procesando datos…")
def process(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df['resolution_days'] = (
        df['Closed Date'] - df['Created Date']
    ).dt.total_seconds() / 86400
    df = df[df['Closed Date'].notna()].copy()
    df = df[df['Agency'].isin(BUSINESS_MAPPING)].copy()
    df['sla_days']    = df['Agency'].map({k: v[0] for k, v in BUSINESS_MAPPING.items()})
    df['cost_usd']    = df['Agency'].map({k: v[1] for k, v in BUSINESS_MAPPING.items()})
    df['sla_breach']  = df['resolution_days'] > df['sla_days']
    df['breach_cost'] = df['sla_breach'] * df['cost_usd']
    df['month']       = df['Created Date'].dt.to_period('M').astype(str)
    return df

import os
DATA_FILE = os.path.join(os.path.dirname(__file__), "data/datos_combinados.parquet")


def _divider(label: str):
    st.markdown(f"""
    <div class="section-divider">
      <div class="section-divider-line"></div>
      <span class="section-divider-label">{label}</span>
      <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)


def _run_dashboard():
    df_full = process(DATA_FILE)

    # ─── SIDEBAR ───
    with st.sidebar:
        st.markdown(f"""
        <div style="margin-bottom:1.2rem;">
          <p style="color:{ACCENT};font-size:0.65rem;text-transform:uppercase;
             letter-spacing:0.12em;font-weight:700;margin:0;">NYC 311 · SLA Intelligence</p>
          <p style="color:{GRAY};font-size:0.72rem;margin:0.2rem 0 0;">Filtros de análisis</p>
        </div>
        """, unsafe_allow_html=True)

        agencies     = sorted(df_full['Agency'].unique())
        sel_agencies = st.multiselect("Agencias", agencies, default=agencies)

        boroughs     = [b for b in sorted(df_full['Borough'].unique()) if b != 'UNSPECIFIED']
        sel_boroughs = st.multiselect("Borough", boroughs, default=boroughs)

        months       = sorted(df_full['month'].unique())
        sel_months   = st.multiselect("Período (meses)", months, default=months)

        max_days     = st.slider("Días resolución máx.", 0, 60, 60)

        st.markdown("---")
        st.markdown(f"""
        <div style="background:{DARK};border-radius:8px;padding:0.7rem 0.9rem;">
          <p style="color:{GRAY2};font-size:0.62rem;text-transform:uppercase;
             letter-spacing:0.1em;margin:0 0 0.4rem;">Datos cargados</p>
          <p style="color:{WHITE};font-size:1.3rem;font-weight:800;margin:0;">{len(df_full):,}</p>
          <p style="color:{GRAY};font-size:0.7rem;margin:0;">registros · {df_full["Agency"].nunique()} agencias</p>
        </div>
        """, unsafe_allow_html=True)

    # ─── FILTER ───
    mask = (
        df_full['Agency'].isin(sel_agencies) &
        df_full['Borough'].isin(sel_boroughs) &
        df_full['month'].isin(sel_months) &
        (df_full['resolution_days'] <= max_days)
    )
    df = df_full[mask].copy()

    summary = df.groupby('Agency').agg(
        total            =('Unique Key',     'count'),
        breaches         =('sla_breach',     'sum'),
        breach_rate      =('sla_breach',     'mean'),
        total_breach_cost=('breach_cost',    'sum'),
        median_days      =('resolution_days','median')
    ).reset_index()
    summary['cost_M']   = summary['total_breach_cost'] / 1e6
    summary['sla_days'] = summary['Agency'].map({k: v[0] for k, v in BUSINESS_MAPPING.items()})

    total_cost     = df['breach_cost'].sum()
    total_breaches = int(df['sla_breach'].sum())
    total_cases    = len(df)
    breach_rate_g  = df['sla_breach'].mean()

    # ═══════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════
    col_title, col_badge = st.columns([5, 1])
    with col_title:
        st.markdown(f"""
        <div style="margin-bottom:0.3rem;">
          <p style="color:{ACCENT};font-size:0.65rem;text-transform:uppercase;
             letter-spacing:0.15em;font-weight:700;margin:0;">NYC 311 Open Data</p>
          <h1 style="font-size:1.75rem;font-weight:800;margin:0.1rem 0;">
            SLA Cost Intelligence Dashboard
          </h1>
          <p style="color:{GRAY};font-size:0.82rem;margin:0.2rem 0 0;">
            ¿Qué incumplimientos generan mayor impacto económico? &nbsp;·&nbsp;
            <span style="color:{WHITE}">{months[0]}</span> →
            <span style="color:{WHITE}">{months[-1]}</span>
          </p>
        </div>
        """, unsafe_allow_html=True)
    with col_badge:
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;
             padding:0.8rem 1rem;text-align:center;margin-top:0.6rem;">
          <p style="color:{GRAY2};font-size:0.6rem;text-transform:uppercase;
             letter-spacing:0.1em;margin:0;">Quejas filtradas</p>
          <p style="color:{WHITE};font-size:1.5rem;font-weight:800;margin:0;">{total_cases:,}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ═══════════════════════════════════════════
    # KPIs
    # ═══════════════════════════════════════════
    worst_cost = summary.nlargest(1,'cost_M').iloc[0]
    worst_rate = summary[summary['total']>100].nlargest(1,'breach_rate').iloc[0]

    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_data = [
        (k1, "Costo Total SLA",  f"${total_cost/1e9:.2f}B",    "en penalidades USD",                                   ACCENT, "↑ impacto total"),
        (k2, "Incumplimientos",  f"{total_breaches:,}",         "casos fuera de SLA",                                   RED,    "casos críticos"),
        (k3, "Tasa Global",       f"{breach_rate_g*100:.1f}%",  "de quejas incumplen",                                  YELLOW, "promedio general"),
        (k4, "Mayor Costo",       worst_cost['Agency'],          f"${worst_cost['cost_M']:.0f}M · {worst_cost['breach_rate']*100:.1f}% breach", RED,    "agencia líder en $"),
        (k5, "Mayor % Breach",    worst_rate['Agency'],          f"{worst_rate['breach_rate']*100:.1f}% · {int(worst_rate['breaches']):,} casos", YELLOW, "tasa más crítica"),
    ]
    for col, label, value, sub, color, badge in kpi_data:
        col.markdown(
            f'<div class="kpi-card">'
            f'<p style="color:{GRAY2};font-size:0.62rem;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-bottom:6px;font-weight:600;">{label}</p>'
            f'<p style="color:{color};font-size:1.75rem;font-weight:800;margin:0;line-height:1.1;">{value}</p>'
            f'<p style="color:{GRAY};font-size:0.68rem;margin:4px 0 0;">{sub}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ═══════════════════════════════════════════
    # ROW 1 — Pareto + Bubble
    # ═══════════════════════════════════════════
    _divider("01 · Distribución del impacto económico")

    cl, cr = st.columns([3, 2])

    with cl:
        st.markdown(f'<p class="story-label">3 agencias concentran el 76% del costo total</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">El NYPD lidera en costo absoluto pese a tener el SLA más corto del sistema (0.33 días)</p>', unsafe_allow_html=True)
        s = summary.sort_values('cost_M', ascending=True)
        colors_b = [ACCENT if v>200 else (BLUE if v>50 else GRAY2) for v in s['cost_M']]
        fig = go.Figure(go.Bar(
            y=s['Agency'], x=s['cost_M'], orientation='h',
            marker_color=colors_b, marker_line_width=0,
            text=[f"${v:.0f}M" for v in s['cost_M']],
            textposition='outside', textfont=dict(color=WHITE, size=11),
            hovertemplate="<b>%{y}</b><br>Costo: $%{x:.1f}M<br>Breaches: %{customdata:,}<extra></extra>",
            customdata=s['breaches']
        ))
        fig.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=330,
            xaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Millones USD", title_font_color=GRAY),
            yaxis=dict(color=WHITE, tickfont=dict(size=12)),
            margin=dict(l=60, r=85, t=10, b=40), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        st.markdown(f'<p class="story-label">Riesgo Operativo — Volumen vs. Tasa de Incumplimiento</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">El tamaño de cada burbuja representa el costo total en millones USD</p>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Scatter(
            x=summary['total'], y=summary['breach_rate']*100,
            mode='markers+text',
            marker=dict(
                size=np.sqrt(summary['cost_M'])*4.5,
                color=summary['breach_rate'],
                colorscale=[[0, GREEN],[0.3, YELLOW],[1, RED]],
                showscale=True,
                colorbar=dict(title=dict(text="Breach Rate", font=dict(color=GRAY, size=10)),
                              tickfont=dict(color=GRAY, size=9), len=0.7),
                line=dict(color=DARK, width=1)
            ),
            text=summary['Agency'], textposition='top center',
            textfont=dict(color=WHITE, size=9),
            hovertemplate="<b>%{text}</b><br>Casos:%{x:,}<br>Breach:%{y:.1f}%<br>Costo:$%{customdata:.0f}M<extra></extra>",
            customdata=summary['cost_M']
        ))
        fig2.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=330,
            xaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Total Quejas", title_font_color=GRAY),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Tasa Incumplimiento (%)", title_font_color=GRAY),
            margin=dict(l=50, r=10, t=10, b=50), showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ═══════════════════════════════════════════
    # ROW 2 — Temporal + Borough
    # ═══════════════════════════════════════════
    _divider("02 · Tendencia temporal y geografía")

    ca, cb = st.columns([3, 2])

    with ca:
        st.markdown(f'<p class="story-label">Evolución mensual de incumplimientos — Top 5 agencias por costo</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">¿Las tasas de breach mejoran o empeoran con el tiempo? Identificá patrones estacionales</p>', unsafe_allow_html=True)
        top5    = summary.nlargest(5,'cost_M')['Agency'].tolist()
        palette = [ACCENT, RED, BLUE, YELLOW, GREEN]
        monthly = df[df['Agency'].isin(top5)].groupby(['month','Agency'])['sla_breach'].mean().reset_index()
        fig3 = go.Figure()
        for i, ag in enumerate(top5):
            d = monthly[monthly['Agency']==ag]
            fig3.add_trace(go.Scatter(
                x=d['month'], y=d['sla_breach']*100, mode='lines+markers',
                name=ag, line=dict(color=palette[i], width=2.5),
                marker=dict(size=7, color=palette[i]),
                hovertemplate=f"<b>{ag}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>"
            ))
        fig3.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=295,
            xaxis=dict(showgrid=False, color=GRAY),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Breach %", title_font_color=GRAY),
            legend=dict(bgcolor=DARK, bordercolor=BORDER, font=dict(color=WHITE, size=10),
                        orientation='h', yanchor='top', y=-0.25, xanchor='center', x=0.5),
            margin=dict(l=50, r=20, t=10, b=80)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with cb:
        st.markdown(f'<p class="story-label">Costo por Borough — ¿Dónde se concentra el impacto geográfico?</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">Algunos distritos generan desproporcionadamente más penalidades</p>', unsafe_allow_html=True)
        bc = df[df['Borough']!='UNSPECIFIED'].groupby('Borough')['breach_cost'].sum().reset_index()
        bc = bc.sort_values('breach_cost', ascending=False)
        bc['cost_M'] = bc['breach_cost'] / 1e6
        fig4 = go.Figure(go.Bar(
            x=bc['Borough'], y=bc['cost_M'],
            marker_color=[ACCENT, RED, BLUE, YELLOW, GREEN][:len(bc)],
            marker_line_width=0,
            text=[f"${v:.0f}M" for v in bc['cost_M']],
            textposition='outside', textfont=dict(color=WHITE, size=10),
            hovertemplate="<b>%{x}</b><br>$%{y:.1f}M<extra></extra>"
        ))
        fig4.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=295,
            xaxis=dict(color=WHITE, tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="M USD", title_font_color=GRAY),
            margin=dict(l=40, r=20, t=10, b=50), showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ═══════════════════════════════════════════
    # ROW 3 — Status + Channel
    # ═══════════════════════════════════════════
    _divider("03 · Estado de quejas y canales de reporte")

    cd, ce = st.columns(2)

    with cd:
        st.markdown(f'<p class="story-label">Estado actual de las quejas</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">Distribución por estado de resolución sobre el total filtrado</p>', unsafe_allow_html=True)
        status_counts   = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'count']
        status_palette  = [GREEN, YELLOW, BLUE, ACCENT, GRAY, RED]
        fig_status = go.Figure(go.Pie(
            labels=status_counts['Status'], values=status_counts['count'],
            hole=0.62,
            marker=dict(colors=status_palette[:len(status_counts)], line=dict(color=DARK, width=2)),
            textinfo='label+percent', textfont=dict(color=WHITE, size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,} quejas<br>%{percent}<extra></extra>",
            sort=True
        ))
        fig_status.add_annotation(
            text=f"<b>{len(df):,}</b><br><span style='font-size:10px'>quejas</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(color=WHITE, size=13), align='center'
        )
        fig_status.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor=DARK, bordercolor=BORDER, font=dict(color=WHITE, size=10),
                        orientation='v', x=1.02, y=0.5),
            showlegend=True
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with ce:
        st.markdown(f'<p class="story-label">Canal de reporte — ¿Cómo llegan las quejas al sistema?</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">El canal dominante puede indicar oportunidades de digitalización</p>', unsafe_allow_html=True)
        channel_counts = df['Open Data Channel Type'].value_counts().reset_index()
        channel_counts.columns = ['Channel', 'count']
        channel_labels = {
            'PHONE':   'Teléfono',
            'ONLINE':  'Online',
            'MOBILE':  'Móvil',
            'UNKNOWN': 'Desconocido',
        }
        channel_counts['label'] = channel_counts['Channel'].map(lambda x: channel_labels.get(x, x))
        channel_palette = [BLUE, ACCENT, GREEN, GRAY]
        fig_channel = go.Figure(go.Pie(
            labels=channel_counts['label'], values=channel_counts['count'],
            hole=0.62,
            marker=dict(colors=channel_palette[:len(channel_counts)], line=dict(color=DARK, width=2)),
            textinfo='label+percent', textfont=dict(color=WHITE, size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,} quejas<br>%{percent}<extra></extra>",
            sort=True
        ))
        top_channel = channel_counts.iloc[0]['label']
        top_pct     = channel_counts.iloc[0]['count'] / channel_counts['count'].sum() * 100
        fig_channel.add_annotation(
            text=f"<b>{top_pct:.0f}%</b><br><span style='font-size:9px'>{top_channel}</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(color=WHITE, size=13), align='center'
        )
        fig_channel.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor=DARK, bordercolor=BORDER, font=dict(color=WHITE, size=10),
                        orientation='v', x=1.02, y=0.5),
            showlegend=True
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    # ═══════════════════════════════════════════
    # ROW 4 — Table + Distribution
    # ═══════════════════════════════════════════
    _divider("04 · Rendimiento por agencia")

    cx, cy = st.columns([2, 3])

    with cx:
        st.markdown(f'<p class="story-label">Tabla comparativa de rendimiento</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">Ordenada por costo total. Compará SLA vs mediana real de resolución.</p>', unsafe_allow_html=True)
        tdf = summary.sort_values('cost_M', ascending=False)[
            ['Agency','total','breaches','breach_rate','cost_M','sla_days','median_days']
        ].copy()
        tdf.columns = ['Agencia','Total','Breaches','Breach%','Costo$M','SLA(d)','Mediana(d)']
        tdf['Breach%']    = (tdf['Breach%']*100).round(1).astype(str)+'%'
        tdf['Costo$M']    = tdf['Costo$M'].round(1).apply(lambda x: f"${x}M")
        tdf['Mediana(d)'] = tdf['Mediana(d)'].round(2)
        st.dataframe(tdf, use_container_width=True, height=285, hide_index=True)

    with cy:
        sel = st.selectbox(
            "Ver distribución de resolución para:",
            options=sorted(df['Agency'].unique()),
            index=list(sorted(df['Agency'].unique())).index('NYPD')
                   if 'NYPD' in df['Agency'].unique() else 0
        )
        st.markdown(f'<p class="story-label">Distribución de tiempo de resolución — {sel}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">La línea amarilla muestra el SLA comprometido. Todo lo que la supera es incumplimiento.</p>', unsafe_allow_html=True)
        ag_df   = df[df['Agency']==sel]
        sla_thr = BUSINESS_MAPPING.get(sel,(5,0))[0]
        on_t    = ag_df[~ag_df['sla_breach']]['resolution_days'].clip(upper=sla_thr*6)
        breach  = ag_df[ ag_df['sla_breach']]['resolution_days'].clip(upper=sla_thr*6)
        fig5 = go.Figure()
        bin_size = sla_thr / 20
        fig5.add_trace(go.Histogram(
            x=on_t,
            xbins=dict(start=0, end=sla_thr*6, size=bin_size),
            name='A tiempo',
            marker_color=GREEN,
            opacity=0.75
        ))
        fig5.add_trace(go.Histogram(
            x=breach,
            xbins=dict(start=0, end=sla_thr*6, size=bin_size),
            name='Incumplimiento',
            marker_color=RED,
            opacity=0.85
        ))
        fig5.add_vline(x=sla_thr, line_color=YELLOW, line_width=2.5, line_dash='dash',
                       annotation_text=f"SLA={sla_thr}d",
                       annotation_font_color=YELLOW, annotation_position="top right")
        fig5.update_layout(
            barmode='overlay', paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=280,
            xaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Días de Resolución", title_font_color=GRAY),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Casos",              title_font_color=GRAY),
            legend=dict(bgcolor=DARK, font=dict(color=WHITE, size=10),
                        orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=50, r=20, t=40, b=50)
        )
        br     = ag_df['sla_breach'].mean()*100
        bc_val = ag_df['breach_cost'].sum()/1e6
        st.plotly_chart(fig5, use_container_width=True)
        st.markdown(
            f'<div class="finding-box">'
            f'<b>{sel}</b>: <b style="color:{ACCENT}">{br:.1f}%</b> de quejas superan el SLA de '
            f'<b>{sla_thr}d</b> → impacto estimado <b style="color:{RED}">${bc_val:.1f}M USD</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ═══════════════════════════════════════════
    # HIPÓTESIS
    # ═══════════════════════════════════════════
    _divider("05 · hipótesis — simulación de escenario sla")

    st.markdown(f"""
    <div class="hypothesis-box">
      <p style="color:{ACCENT};font-size:0.62rem;text-transform:uppercase;
         letter-spacing:0.14em;font-weight:700;margin:0 0 6px;">Hipótesis planteada</p>
      <p style="color:{WHITE};font-size:1rem;font-weight:700;margin:0 0 4px;">
        ¿Qué pasaría con el costo total del NYPD si se aumentara su tiempo límite de respuesta?
      </p>
      <p style="color:{GRAY};font-size:0.8rem;margin:0;">
        SLA actual: <span style="color:{RED};font-weight:600;">0.33 días (8 horas)</span> —
        el más estricto del sistema. Mové el slider para simular el impacto de flexibilizarlo.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    nuevo_sla = st.slider(
        "Ajustar SLA del NYPD (días)",
        min_value=0.33, max_value=5.0, value=0.33, step=0.1,
        help="SLA actual: 0.33 días (8 horas). Mueve el slider para simular un umbral diferente."
    )

    nypd_df        = df[df['Agency'] == 'NYPD'].copy()
    costo_por_caso = BUSINESS_MAPPING['NYPD'][1]

    breach_actual  = nypd_df['sla_breach'].sum()
    costo_actual   = breach_actual * costo_por_caso
    tasa_actual    = nypd_df['sla_breach'].mean() * 100

    nypd_df['breach_simulado'] = nypd_df['resolution_days'] > nuevo_sla
    breach_simulado   = nypd_df['breach_simulado'].sum()
    costo_simulado    = breach_simulado * costo_por_caso
    tasa_simulada     = nypd_df['breach_simulado'].mean() * 100

    ahorro            = costo_actual - costo_simulado
    casos_recuperados = int(breach_actual - breach_simulado)

    h1, h2, h3, h4 = st.columns(4)
    for col, label, val_top, val_bot, color in [
        (h1, "Costo Actual (NYPD)",     f"${costo_actual/1e6:.0f}M",    f"base de comparación",           RED),
        (h2, "Costo Simulado",          f"${costo_simulado/1e6:.0f}M",  f"con SLA = {nuevo_sla}d",        GREEN),
        (h3, "Ahorro Estimado",         f"${ahorro/1e6:.0f}M USD",      f"reducción en penalidades",       ACCENT),
        (h4, "Casos Recuperados",       f"{casos_recuperados:,}",        f"dejan de ser breach",           YELLOW),
    ]:
        col.markdown(
            f'<div class="kpi-card">'
            f'<p style="color:{GRAY2};font-size:0.62rem;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-bottom:6px;font-weight:600;">{label}</p>'
            f'<p style="color:{color};font-size:1.6rem;font-weight:800;margin:0;line-height:1.1;">{val_top}</p>'
            f'<p style="color:{GRAY};font-size:0.68rem;margin:4px 0 0;">{val_bot}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    hi1, hi2 = st.columns(2)

    with hi1:
        st.markdown(f'<p class="story-label">Distribución de resolución NYPD — Breach actual vs. simulado</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">Los casos entre ambas líneas son los que dejarían de penalizarse con el nuevo SLA</p>', unsafe_allow_html=True)
        fig_h = go.Figure()
        fig_h.add_trace(go.Histogram(
            x=nypd_df[nypd_df['sla_breach']]['resolution_days'].clip(upper=nuevo_sla * 10),
            nbinsx=50, name='Breach Actual', marker_color=RED, opacity=0.6
        ))
        fig_h.add_trace(go.Histogram(
            x=nypd_df[nypd_df['breach_simulado']]['resolution_days'].clip(upper=nuevo_sla * 10),
            nbinsx=50, name='Breach Simulado', marker_color=YELLOW, opacity=0.6
        ))
        fig_h.add_vline(x=0.33,      line_color=RED,    line_width=2, line_dash='dash',
                        annotation_text="SLA actual 0.33d",
                        annotation_font_color=RED,    annotation_position="top left")
        fig_h.add_vline(x=nuevo_sla, line_color=YELLOW, line_width=2, line_dash='dash',
                        annotation_text=f"SLA simulado {nuevo_sla}d",
                        annotation_font_color=YELLOW, annotation_position="top right")
        fig_h.update_layout(
            barmode='overlay', paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            xaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Días de Resolución", title_font_color=GRAY),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Casos",              title_font_color=GRAY),
            legend=dict(bgcolor=DARK, font=dict(color=WHITE, size=10),
                        orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=50, r=20, t=40, b=50)
        )
        st.plotly_chart(fig_h, use_container_width=True)

    with hi2:
        st.markdown(f'<p class="story-label">Costo actual vs. costo simulado</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="story-sub">La diferencia de altura entre ambas barras es el ahorro anual estimado en penalidades</p>', unsafe_allow_html=True)
        escenarios  = ['SLA Actual<br>(0.33 días)', f'SLA Simulado<br>({nuevo_sla} días)']
        costos      = [costo_actual / 1e6, costo_simulado / 1e6]
        colores_bar = [RED, GREEN if ahorro >= 0 else ACCENT]
        fig_cmp = go.Figure(go.Bar(
            x=escenarios, y=costos,
            marker_color=colores_bar, marker_line_width=0,
            text=[f"${v:.0f}M" for v in costos],
            textposition='outside', textfont=dict(color=WHITE, size=12),
            hovertemplate="<b>%{x}</b><br>Costo: $%{y:.1f}M<extra></extra>"
        ))
        fig_cmp.add_annotation(
            x=1, y=max(costos) * 0.5,
            text=f"<b>Ahorro estimado<br>${ahorro/1e6:.0f}M USD</b>",
            showarrow=False,
            font=dict(color=GREEN if ahorro >= 0 else RED, size=13),
            align='center'
        )
        fig_cmp.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            xaxis=dict(color=WHITE, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=GRAY, title="Millones USD", title_font_color=GRAY),
            margin=dict(l=50, r=20, t=20, b=50), showlegend=False
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

    conclusion_color = GREEN if ahorro > 0 else RED
    st.markdown(f"""
    <div class="finding-box">
      <p style="color:{ACCENT};font-size:0.62rem;text-transform:uppercase;
         letter-spacing:0.14em;font-weight:700;margin:0 0 6px;">Conclusión de la Hipótesis</p>
      <p style="color:{WHITE};font-size:0.95rem;font-weight:600;margin:0 0 6px;">
        Con un SLA de <span style="color:{YELLOW}">{nuevo_sla} días</span>, el NYPD pasaría de
        <span style="color:{RED}">{tasa_actual:.1f}%</span> a
        <span style="color:{GREEN}">{tasa_simulada:.1f}%</span> de breach —
        liberando <span style="color:{ACCENT}">{casos_recuperados:,} casos</span> y generando
        un ahorro estimado de <span style="color:{conclusion_color}">${ahorro/1e6:.0f}M USD</span>.
      </p>
      <p style="color:{GRAY};font-size:0.78rem;margin:4px 0 0;">
        Nota: Flexibilizar el SLA reduce el costo contable de penalización, pero <b>no mejora el tiempo real
        de respuesta</b>. La decisión óptima combina ajuste del umbral <b>y</b> mayor capacidad operativa.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"""
    <div class="finding-box">
      <p style="color:{ACCENT};font-size:0.62rem;text-transform:uppercase;
         letter-spacing:0.14em;font-weight:700;margin:0 0 8px;">Hallazgo clave para gerencia</p>
      <p style="color:{WHITE};font-size:1rem;font-weight:600;margin:0 0 8px;">
        3 agencias (NYPD, HPD, DEP) generan
        <span style="color:{ACCENT}">$2.3B USD</span> — el 76% del costo total por incumplimiento SLA.
      </p>
      <p style="color:{GRAY};font-size:0.82rem;margin:0;">
        <b style="color:{WHITE}">NYPD</b> lidera en costo absoluto ($985M) pese a tener un SLA de solo 0.33 días. &nbsp;
        <b style="color:{WHITE}">DEP</b> tiene la tasa de breach más crítica (63%). &nbsp;
        Acción recomendada: <b style="color:{YELLOW}">redimensionar capacidad de respuesta en NYPD y revisar el modelo SLA de DEP.</b>
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<p style="color:{GRAY2};font-size:0.68rem;text-align:center;margin-top:1.2rem;">'
        f'NYC 311 Open Data &nbsp;·&nbsp; Modelo de costo por penalización SLA &nbsp;·&nbsp; {months[0]} – {months[-1]}</p>',
        unsafe_allow_html=True
    )


_run_dashboard()