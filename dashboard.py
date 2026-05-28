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
BORDER = "#30363d"
ACCENT = "#f97316"
WHITE  = "#f8fafc"
GRAY   = "#94a3b8"
RED    = "#ef4444"
GREEN  = "#22c55e"
YELLOW = "#eab308"
BLUE   = "#3b82f6"

st.markdown(f"""
<style>
  html, body, [class*="css"] {{
    background-color:{DARK}; color:{WHITE}; font-family:'Inter',sans-serif;
  }}
  .block-container {{ padding:1.2rem 2rem 2rem; }}
  section[data-testid="stSidebar"] {{
    background-color:{PANEL}; border-right:1px solid {BORDER};
  }}
  .stSelectbox label,.stMultiSelect label,.stSlider label {{
    color:{GRAY}!important; font-size:0.78rem;
    text-transform:uppercase; letter-spacing:0.06em;
  }}
  .kpi-card {{
    background:{PANEL}; border:1px solid {BORDER};
    border-radius:10px; padding:1rem 1.2rem; text-align:center;
  }}
  .section-header {{
    font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em;
    color:{GRAY}; margin-bottom:0.3rem; padding-bottom:0.4rem;
    border-bottom:1px solid {BORDER};
  }}
  h1,h2,h3 {{ color:{WHITE}!important; }}
  .finding-box {{
    background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
    border-left:4px solid {ACCENT}; border-radius:0 8px 8px 0;
    padding:1rem 1.4rem; margin:0.5rem 0;
  }}
  [data-testid="stFileUploadDropzone"] {{
    background:{PANEL}!important; border:2px dashed {BORDER}!important;
    border-radius:10px!important;
  }}
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

# ─── DATA PATH ───
import os
DATA_FILE = os.path.join(os.path.dirname(__file__), "data/datos_combinados.parquet")


def _run_dashboard():
    # ─── PROCESS ───
    df_full = process(DATA_FILE)

    # ─── SIDEBAR FILTERS ───
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")

        agencies = sorted(df_full['Agency'].unique())
        sel_agencies = st.multiselect("Agencias", agencies, default=agencies)

        boroughs = [b for b in sorted(df_full['Borough'].unique()) if b != 'UNSPECIFIED']
        sel_boroughs = st.multiselect("Borough", boroughs, default=boroughs)

        months = sorted(df_full['month'].unique())
        sel_months = st.multiselect("Período (meses)", months, default=months)

        max_days = st.slider("Días resolución máx.", 0, 60, 60)

        st.markdown("---")
        st.markdown(
            f'<p style="color:{GRAY};font-size:0.7rem;">'
            f'Registros cargados: <b style="color:{WHITE}">{len(df_full):,}</b><br>'
            f'Agencias mapeadas: <b style="color:{WHITE}">{df_full["Agency"].nunique()}</b></p>',
            unsafe_allow_html=True
        )

    # ─── FILTER ───
    mask = (
        df_full['Agency'].isin(sel_agencies) &
        df_full['Borough'].isin(sel_boroughs) &
        df_full['month'].isin(sel_months) &
        (df_full['resolution_days'] <= max_days)
    )
    df = df_full[mask].copy()

    summary = df.groupby('Agency').agg(
        total        =('Unique Key',    'count'),
        breaches     =('sla_breach',    'sum'),
        breach_rate  =('sla_breach',    'mean'),
        total_breach_cost=('breach_cost','sum'),
        median_days  =('resolution_days','median')
    ).reset_index()
    summary['cost_M']   = summary['total_breach_cost'] / 1e6
    summary['sla_days'] = summary['Agency'].map({k: v[0] for k, v in BUSINESS_MAPPING.items()})

    total_cost    = df['breach_cost'].sum()
    total_breaches = int(df['sla_breach'].sum())
    total_cases   = len(df)
    breach_rate_g = df['sla_breach'].mean()

    # ─── HEADER ───
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("## 🚨 NYC 311 — SLA Cost Intelligence Dashboard")
        st.markdown(
            f'<p style="color:{GRAY};font-size:0.85rem;margin-top:-0.5rem;">'
            f'¿Qué incumplimientos generan mayor impacto económico? · {months[0]} → {months[-1]}</p>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div style="background:{PANEL};border:1px solid {BORDER};border-radius:8px;'
            f'padding:0.6rem 1rem;text-align:center;margin-top:0.5rem;">'
            f'<p style="color:{GRAY};font-size:0.65rem;margin:0;">REGISTROS</p>'
            f'<p style="color:{WHITE};font-size:1.4rem;font-weight:700;margin:0;">{total_cases:,}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown("---")

    # ─── KPIs ───
    k1,k2,k3,k4,k5 = st.columns(5)
    worst_cost = summary.nlargest(1,'cost_M').iloc[0]
    worst_rate = summary[summary['total']>100].nlargest(1,'breach_rate').iloc[0]

    for col, label, value, sub, color in [
        (k1,"💸 Costo Total SLA",   f"${total_cost/1e9:.2f}B",   "USD en penalidades",       ACCENT),
        (k2,"⚠️ Incumplimientos",   f"{total_breaches:,}",        "casos fuera de SLA",       RED),
        (k3,"📊 Tasa Global",        f"{breach_rate_g*100:.1f}%", "de quejas incumplen SLA",  YELLOW),
        (k4,"🔴 Mayor Impacto $",   worst_cost['Agency'],         f"${worst_cost['cost_M']:.0f}M · {worst_cost['breach_rate']*100:.1f}% breach", RED),
        (k5,"📈 Mayor % Breach",    worst_rate['Agency'],         f"{worst_rate['breach_rate']*100:.1f}% · {int(worst_rate['breaches']):,} casos", YELLOW),
    ]:
        col.markdown(
            f'<div class="kpi-card">'
            f'<p style="color:{GRAY};font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">{label}</p>'
            f'<p style="color:{color};font-size:1.8rem;font-weight:800;margin:0;">{value}</p>'
            f'<p style="color:{GRAY};font-size:0.7rem;margin:0;">{sub}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── ROW 1: Pareto + Bubble ───
    cl, cr = st.columns([3,2])

    with cl:
        st.markdown(f'<p class="section-header">💰 Pareto de Costo — 3 Agencias concentran el 76% del impacto</p>', unsafe_allow_html=True)
        s = summary.sort_values('cost_M', ascending=True)
        colors_b = [ACCENT if v>200 else (BLUE if v>50 else GRAY) for v in s['cost_M']]
        fig = go.Figure(go.Bar(
            y=s['Agency'], x=s['cost_M'], orientation='h',
            marker_color=colors_b, marker_line_width=0,
            text=[f"${v:.0f}M" for v in s['cost_M']],
            textposition='outside', textfont=dict(color=WHITE,size=11),
            hovertemplate="<b>%{y}</b><br>Costo: $%{x:.1f}M<br>Breaches: %{customdata:,}<extra></extra>",
            customdata=s['breaches']
        ))
        fig.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=320,
            xaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Millones USD",title_font_color=GRAY),
            yaxis=dict(color=WHITE,tickfont=dict(size=12)),
            margin=dict(l=60,r=80,t=10,b=40), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        st.markdown(f'<p class="section-header">🎯 Riesgo Operativo — Volumen vs. Tasa de Incumplimiento</p>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Scatter(
            x=summary['total'], y=summary['breach_rate']*100,
            mode='markers+text',
            marker=dict(
                size=np.sqrt(summary['cost_M'])*4.5,
                color=summary['breach_rate'],
                colorscale=[[0,GREEN],[0.3,YELLOW],[1,RED]],
                showscale=True,
                colorbar=dict(title=dict(text="Breach Rate",font=dict(color=GRAY,size=10)),
                              tickfont=dict(color=GRAY,size=9),len=0.7),
                line=dict(color=DARK,width=1)
            ),
            text=summary['Agency'], textposition='top center',
            textfont=dict(color=WHITE,size=9),
            hovertemplate="<b>%{text}</b><br>Casos:%{x:,}<br>Breach:%{y:.1f}%<br>Costo:$%{customdata:.0f}M<extra></extra>",
            customdata=summary['cost_M']
        ))
        fig2.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=320,
            xaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Total Quejas",title_font_color=GRAY),
            yaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Tasa Incumplimiento (%)",title_font_color=GRAY),
            margin=dict(l=50,r=10,t=10,b=50), showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ─── ROW 2: Temporal + Borough ───
    ca, cb = st.columns([3,2])

    with ca:
        st.markdown(f'<p class="section-header">📈 Evolución Mensual — Tendencia de Incumplimientos Top 5</p>', unsafe_allow_html=True)
        top5 = summary.nlargest(5,'cost_M')['Agency'].tolist()
        palette = [ACCENT,RED,BLUE,YELLOW,GREEN]
        monthly = df[df['Agency'].isin(top5)].groupby(['month','Agency'])['sla_breach'].mean().reset_index()
        fig3 = go.Figure()
        for i,ag in enumerate(top5):
            d = monthly[monthly['Agency']==ag]
            fig3.add_trace(go.Scatter(
                x=d['month'], y=d['sla_breach']*100, mode='lines+markers',
                name=ag, line=dict(color=palette[i],width=2.5),
                marker=dict(size=7,color=palette[i]),
                hovertemplate=f"<b>{ag}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>"
            ))
        fig3.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=290,
            xaxis=dict(showgrid=False,color=GRAY),
            yaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Breach %",title_font_color=GRAY),
            legend=dict(bgcolor=DARK,bordercolor=BORDER,font=dict(color=WHITE,size=10),
                        orientation='h',yanchor='top',y=-0.25,xanchor='center',x=0.5),
            margin=dict(l=50,r=20,t=10,b=80)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with cb:
        st.markdown(f'<p class="section-header">🏙️ Distribución por Borough — Costo Total</p>', unsafe_allow_html=True)
        bc = df[df['Borough']!='UNSPECIFIED'].groupby('Borough')['breach_cost'].sum().reset_index()
        bc = bc.sort_values('breach_cost',ascending=False)
        bc['cost_M'] = bc['breach_cost']/1e6
        fig4 = go.Figure(go.Bar(
            x=bc['Borough'], y=bc['cost_M'],
            marker_color=[ACCENT,RED,BLUE,YELLOW,GREEN][:len(bc)],
            marker_line_width=0,
            text=[f"${v:.0f}M" for v in bc['cost_M']],
            textposition='outside', textfont=dict(color=WHITE,size=10),
            hovertemplate="<b>%{x}</b><br>$%{y:.1f}M<extra></extra>"
        ))
        fig4.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=290,
            xaxis=dict(color=WHITE,tickfont=dict(size=9)),
            yaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="M USD",title_font_color=GRAY),
            margin=dict(l=40,r=20,t=10,b=50), showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ─── ROW 3: Status + Channel ───
    cd, ce = st.columns(2)

    with cd:
        st.markdown(f'<p class="section-header">🔵 Estado de Quejas</p>', unsafe_allow_html=True)
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'count']
        status_palette = [GREEN, YELLOW, BLUE, ACCENT, GRAY, RED]
        fig_status = go.Figure(go.Pie(
            labels=status_counts['Status'],
            values=status_counts['count'],
            hole=0.62,
            marker=dict(
                colors=status_palette[:len(status_counts)],
                line=dict(color=DARK, width=2)
            ),
            textinfo='label+percent',
            textfont=dict(color=WHITE, size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,} quejas<br>%{percent}<extra></extra>",
            sort=True
        ))
        total_filtered = len(df)
        fig_status.add_annotation(
            text=f"<b>{total_filtered:,}</b><br><span style='font-size:10px'>quejas</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=WHITE, size=13),
            align='center'
        )
        fig_status.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(
                bgcolor=DARK, bordercolor=BORDER,
                font=dict(color=WHITE, size=10),
                orientation='v', x=1.02, y=0.5
            ),
            showlegend=True
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with ce:
        st.markdown(f'<p class="section-header">📡 Canal de Reporte</p>', unsafe_allow_html=True)
        channel_counts = df['Open Data Channel Type'].value_counts().reset_index()
        channel_counts.columns = ['Channel', 'count']
        channel_labels = {
            'PHONE': '📞 Teléfono',
            'ONLINE': '🌐 Online',
            'MOBILE': '📱 Móvil',
            'UNKNOWN': '❓ Desconocido',
        }
        channel_counts['label'] = channel_counts['Channel'].map(
            lambda x: channel_labels.get(x, x)
        )
        channel_palette = [BLUE, ACCENT, GREEN, GRAY]
        fig_channel = go.Figure(go.Pie(
            labels=channel_counts['label'],
            values=channel_counts['count'],
            hole=0.62,
            marker=dict(
                colors=channel_palette[:len(channel_counts)],
                line=dict(color=DARK, width=2)
            ),
            textinfo='label+percent',
            textfont=dict(color=WHITE, size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,} quejas<br>%{percent}<extra></extra>",
            sort=True
        ))
        top_channel = channel_counts.iloc[0]['label']
        top_pct = channel_counts.iloc[0]['count'] / channel_counts['count'].sum() * 100
        fig_channel.add_annotation(
            text=f"<b>{top_pct:.0f}%</b><br><span style='font-size:9px'>{top_channel}</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=WHITE, size=13),
            align='center'
        )
        fig_channel.update_layout(
            paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(
                bgcolor=DARK, bordercolor=BORDER,
                font=dict(color=WHITE, size=10),
                orientation='v', x=1.02, y=0.5
            ),
            showlegend=True
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    # ─── ROW 4: Table + Histogram ───
    cx, cy = st.columns([2,3])

    with cx:
        st.markdown(f'<p class="section-header">📋 Tabla de Rendimiento por Agencia</p>', unsafe_allow_html=True)
        tdf = summary.sort_values('cost_M',ascending=False)[
            ['Agency','total','breaches','breach_rate','cost_M','sla_days','median_days']
        ].copy()
        tdf.columns = ['Agencia','Total','Breaches','Breach%','Costo$M','SLA(d)','Mediana(d)']
        tdf['Breach%']    = (tdf['Breach%']*100).round(1).astype(str)+'%'
        tdf['Costo$M']    = tdf['Costo$M'].round(1).apply(lambda x: f"${x}M")
        tdf['Mediana(d)'] = tdf['Mediana(d)'].round(2)
        st.dataframe(tdf, use_container_width=True, height=280, hide_index=True)

    with cy:
        sel = st.selectbox(
            "🔍 Ver distribución de resolución para:",
            options=sorted(df['Agency'].unique()),
            index=list(sorted(df['Agency'].unique())).index('NYPD')
                   if 'NYPD' in df['Agency'].unique() else 0
        )
        st.markdown(f'<p class="section-header">📊 Distribución Tiempo de Resolución — {sel}</p>', unsafe_allow_html=True)
        ag_df   = df[df['Agency']==sel]
        sla_thr = BUSINESS_MAPPING.get(sel,(5,0))[0]
        on_t    = ag_df[~ag_df['sla_breach']]['resolution_days'].clip(upper=sla_thr*6)
        breach  = ag_df[ ag_df['sla_breach']]['resolution_days'].clip(upper=sla_thr*6)

        fig5 = go.Figure()
        fig5.add_trace(go.Histogram(x=on_t,   nbinsx=50, name='✅ A tiempo',      marker_color=GREEN, opacity=0.75))
        fig5.add_trace(go.Histogram(x=breach, nbinsx=50, name='❌ Incumplimiento', marker_color=RED,   opacity=0.85))
        fig5.add_vline(x=sla_thr, line_color=YELLOW, line_width=2.5, line_dash='dash',
                       annotation_text=f"SLA={sla_thr}d",
                       annotation_font_color=YELLOW, annotation_position="top right")
        fig5.update_layout(
            barmode='overlay', paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=280,
            xaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Días de Resolución",title_font_color=GRAY),
            yaxis=dict(showgrid=True,gridcolor=BORDER,color=GRAY,title="Casos",title_font_color=GRAY),
            legend=dict(bgcolor=DARK,font=dict(color=WHITE,size=10),
                        orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1),
            margin=dict(l=50,r=20,t=40,b=50)
        )
        br = ag_df['sla_breach'].mean()*100
        bc_val = ag_df['breach_cost'].sum()/1e6
        st.plotly_chart(fig5, use_container_width=True)
        st.markdown(
            f'<div class="finding-box">⚡ <b>{sel}</b>: '
            f'<b style="color:{ACCENT}">{br:.1f}%</b> de quejas superan el SLA de '
            f'<b>{sla_thr}d</b> → impacto estimado '
            f'<b style="color:{RED}">${bc_val:.1f}M USD</b></div>',
            unsafe_allow_html=True
        )

    # ─── FOOTER ───
    st.markdown("---")
    st.markdown(f"""
    <div class="finding-box">
      <p style="color:{ACCENT};font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 6px;">
        🔍 HALLAZGO CLAVE PARA GERENCIA
      </p>
      <p style="color:{WHITE};font-size:1rem;font-weight:600;margin:0 0 8px;">
        3 agencias (NYPD, HPD, DEP) generan
        <span style="color:{ACCENT}">$2.3B USD</span> — el 76% del costo total por incumplimiento SLA.
      </p>
      <p style="color:{GRAY};font-size:0.85rem;margin:0;">
        📌 <b style="color:{WHITE}">NYPD</b> lidera en costo absoluto ($985M) pese a tener un SLA de solo 0.33 días.
        <b style="color:{WHITE}">DEP</b> tiene la tasa de breach más crítica (63%).
        Acción táctica recomendada:
        <b style="color:{YELLOW}">redimensionar capacidad de respuesta en NYPD y revisar el modelo SLA de DEP.</b>
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{GRAY};font-size:0.7rem;text-align:center;margin-top:1rem;">'
        f'NYC 311 Open Data · Modelo de costo por penalización SLA</p>',
        unsafe_allow_html=True
    )

_run_dashboard()