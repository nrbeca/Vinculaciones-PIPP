"""
Validador de Claves Presupuestarias PIPP 2026
Aplicación completa para validar combinaciones usando los 3 catálogos oficiales.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

st.set_page_config(
    page_title="Validador PIPP 2026 | SADER",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
    :root {
        --guinda: #6B1D3D;
        --guinda-claro: #8B2D4D;
        --crema: #F5F0E6;
        --verde-ok: #2E7D32;
        --rojo-error: #C62828;
    }
    .main-header {
        background: linear-gradient(135deg, var(--guinda) 0%, var(--guinda-claro) 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(107, 29, 61, 0.3);
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem; }
    .stat-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid var(--guinda);
        margin-bottom: 1rem;
    }
    .stat-number { font-size: 2rem; font-weight: 700; color: var(--guinda); line-height: 1; }
    .stat-label { color: #666; font-size: 0.9rem; margin-top: 0.3rem; }
    .result-valid {
        background: #E8F5E9;
        border: 1px solid #A5D6A7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .result-invalid {
        background: #FFEBEE;
        border: 1px solid #EF9A9A;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background: var(--guinda);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover { background: var(--guinda-claro); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

EFS_VALIDOS = ['00'] + [str(i).zfill(2) for i in range(1, 35)]
RGS_VALIDOS = ['00', '01', '02', '03']
NOMBRE_CAPITULO = {
    '1': 'Servicios Personales', '2': 'Materiales y Suministros', '3': 'Servicios Generales',
    '4': 'Transferencias', '5': 'Bienes Muebles', '6': 'Inversión Pública',
    '7': 'Inversiones Financieras', '8': 'Participaciones', '9': 'Deuda Pública'
}

def normalizar(valor, digitos=None):
    if valor is None: return ''
    valor = str(valor).strip()
    if valor.lower() in ['nan', 'none', '']: return ''
    if digitos and valor.isdigit(): return valor.zfill(digitos)
    return valor

@st.cache_data
def cargar_catalogo_pp_partida(archivo):
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    partidas_por_pp = {}
    for _, row in df.iterrows():
        mod = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        prog = normalizar(row.iloc[4], 3)
        partida = normalizar(row.iloc[6], 5)
        if mod and prog and partida:
            pp = f"{mod}{prog}"
            if pp not in partidas_por_pp: partidas_por_pp[pp] = set()
            partidas_por_pp[pp].add(partida)
    return partidas_por_pp

@st.cache_data
def cargar_catalogo_relaciones(archivo):
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    cat_urs, cat_ur_fin, cat_ur_fin_fun = set(), set(), set()
    cat_ur_fin_fun_sf, cat_ur_fin_fun_sf_ai, cat_ur_fin_fun_sf_ai_pp = set(), set(), set()
    for _, row in df.iterrows():
        ur = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        fin = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        fun = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
        sf = normalizar(row.iloc[8], 2)
        ai = normalizar(row.iloc[10], 3)
        mod = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ''
        prog = normalizar(row.iloc[14], 3)
        pp = f"{mod}{prog}"
        if ur:
            cat_urs.add(ur)
            if fin:
                cat_ur_fin.add((ur, fin))
                if fun:
                    cat_ur_fin_fun.add((ur, fin, fun))
                    if sf:
                        cat_ur_fin_fun_sf.add((ur, fin, fun, sf))
                        if ai:
                            cat_ur_fin_fun_sf_ai.add((ur, fin, fun, sf, ai))
                            if pp: cat_ur_fin_fun_sf_ai_pp.add((ur, fin, fun, sf, ai, pp))
    return {'urs': cat_urs, 'ur_fin': cat_ur_fin, 'ur_fin_fun': cat_ur_fin_fun,
            'ur_fin_fun_sf': cat_ur_fin_fun_sf, 'ur_fin_fun_sf_ai': cat_ur_fin_fun_sf_ai,
            'ur_fin_fun_sf_ai_pp': cat_ur_fin_fun_sf_ai_pp}

@st.cache_data
def cargar_catalogo_estructura(archivo):
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    partida_tg_ff, partida_tg, tg_ff_por_partida = {}, {}, {}
    all_tgs, all_ffs = set(), set()
    for _, row in df.iterrows():
        partida = normalizar(row.iloc[2], 5)
        tg = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        ff = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
        if partida and tg and ff:
            if partida not in partida_tg_ff: partida_tg_ff[partida] = set()
            partida_tg_ff[partida].add((tg, ff))
            if partida not in partida_tg: partida_tg[partida] = set()
            partida_tg[partida].add(tg)
            if partida not in tg_ff_por_partida: tg_ff_por_partida[partida] = {}
            if tg not in tg_ff_por_partida[partida]: tg_ff_por_partida[partida][tg] = set()
            tg_ff_por_partida[partida][tg].add(ff)
            all_tgs.add(tg)
            all_ffs.add(ff)
    return {'partida_tg_ff': partida_tg_ff, 'partida_tg': partida_tg,
            'tg_ff_por_partida': tg_ff_por_partida, 'all_tgs': all_tgs, 'all_ffs': all_ffs}

def validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura):
    c = {
        'RAMO': normalizar(clave.get('RAMO'), 2), 'UR': normalizar(clave.get('UR')),
        'AÑO': normalizar(clave.get('AÑO')), 'FIN': normalizar(clave.get('FIN')),
        'FUN': normalizar(clave.get('FUN')), 'SF': normalizar(clave.get('SF'), 2),
        'RG': normalizar(clave.get('RG'), 2), 'AI': normalizar(clave.get('AI'), 3),
        'PP': normalizar(clave.get('PP')).upper(), 'PARTIDA': normalizar(clave.get('PARTIDA'), 5),
        'TG': normalizar(clave.get('TG')), 'FF': normalizar(clave.get('FF')),
        'EF': normalizar(clave.get('EF'), 2), 'PPI': normalizar(clave.get('PPI')),
        'AUX2': normalizar(clave.get('AUX2'), 5), 'COP': normalizar(clave.get('COP'), 2),
    }
    res, sug = {}, {}
    cat_urs = cat_relaciones['urs']
    cat_ur_fin = cat_relaciones['ur_fin']
    cat_ur_fin_fun = cat_relaciones['ur_fin_fun']
    cat_ur_fin_fun_sf = cat_relaciones['ur_fin_fun_sf']
    cat_ur_fin_fun_sf_ai = cat_relaciones['ur_fin_fun_sf_ai']
    cat_ur_fin_fun_sf_ai_pp = cat_relaciones['ur_fin_fun_sf_ai_pp']
    partida_tg = cat_estructura['partida_tg']
    tg_ff_por_partida = cat_estructura['tg_ff_por_partida']
    all_tgs = cat_estructura['all_tgs']
    
    if c['RAMO']:
        res['RAMO'] = 'SI' if c['RAMO'] == '08' else 'NO'
        if res['RAMO'] == 'NO': sug['RAMO'] = '08'
    if c['UR']:
        res['UR'] = 'SI' if c['UR'] in cat_urs else 'NO'
        if res['UR'] == 'NO': sug['UR'] = ', '.join(sorted(cat_urs)[:15])
    if c['AÑO']:
        res['AÑO'] = 'SI' if c['AÑO'] == '2026' else 'NO'
        if res['AÑO'] == 'NO': sug['AÑO'] = '2026'
    if c['FIN']:
        if c['UR'] and c['UR'] in cat_urs:
            fins_v = sorted(set(f for u, f in cat_ur_fin if u == c['UR']))
            res['FIN'] = 'SI' if c['FIN'] in fins_v else 'NO'
            if res['FIN'] == 'NO': sug['FIN'] = ', '.join(fins_v)
        else:
            all_fins = sorted(set(f for u, f in cat_ur_fin))
            res['FIN'] = 'SI' if c['FIN'] in all_fins else 'NO'
            if res['FIN'] == 'NO': sug['FIN'] = ', '.join(all_fins)
    if c['FUN']:
        if c['UR'] and c['FIN'] and res.get('FIN') == 'SI':
            funs_v = sorted(set(f for u, fi, f in cat_ur_fin_fun if u == c['UR'] and fi == c['FIN']))
            res['FUN'] = 'SI' if c['FUN'] in funs_v else 'NO'
            if res['FUN'] == 'NO': sug['FUN'] = ', '.join(funs_v)
        else:
            all_funs = sorted(set(f for u, fi, f in cat_ur_fin_fun))
            res['FUN'] = 'SI' if c['FUN'] in all_funs else 'NO'
            if res['FUN'] == 'NO': sug['FUN'] = ', '.join(all_funs)
    if c['SF']:
        if c['UR'] and c['FIN'] and c['FUN'] and res.get('FUN') == 'SI':
            sfs_v = sorted(set(s for u, fi, fu, s in cat_ur_fin_fun_sf if u == c['UR'] and fi == c['FIN'] and fu == c['FUN']))
            res['SF'] = 'SI' if c['SF'] in sfs_v else 'NO'
            if res['SF'] == 'NO': sug['SF'] = ', '.join(sfs_v)
        else:
            all_sfs = sorted(set(s for u, fi, fu, s in cat_ur_fin_fun_sf))
            res['SF'] = 'SI' if c['SF'] in all_sfs else 'NO'
            if res['SF'] == 'NO': sug['SF'] = ', '.join(all_sfs[:15])
    if c['RG']:
        res['RG'] = 'SI' if c['RG'] in RGS_VALIDOS else 'NO'
        if res['RG'] == 'NO': sug['RG'] = ', '.join(RGS_VALIDOS)
    if c['AI']:
        if c['UR'] and c['SF'] and res.get('SF') == 'SI':
            ais_v = sorted(set(a for u, fi, fu, s, a in cat_ur_fin_fun_sf_ai if u == c['UR'] and fi == c['FIN'] and fu == c['FUN'] and s == c['SF']))
            res['AI'] = 'SI' if c['AI'] in ais_v else 'NO'
            if res['AI'] == 'NO': sug['AI'] = ', '.join(ais_v)
        else:
            all_ais = sorted(set(a for u, fi, fu, s, a in cat_ur_fin_fun_sf_ai))
            res['AI'] = 'SI' if c['AI'] in all_ais else 'NO'
            if res['AI'] == 'NO': sug['AI'] = ', '.join(all_ais[:15])
    if c['PP']:
        if c['UR'] and c['AI'] and res.get('AI') == 'SI':
            pps_v = sorted(set(p for u, fi, fu, s, a, p in cat_ur_fin_fun_sf_ai_pp if u == c['UR'] and fi == c['FIN'] and fu == c['FUN'] and s == c['SF'] and a == c['AI']))
            res['PP'] = 'SI' if c['PP'] in pps_v else 'NO'
            if res['PP'] == 'NO': sug['PP'] = ', '.join(pps_v)
        else:
            res['PP'] = 'SI' if c['PP'] in cat_pp_partida else 'NO'
            if res['PP'] == 'NO': sug['PP'] = ', '.join(sorted(cat_pp_partida.keys())[:15])
    if c['PARTIDA']:
        if c['PP'] and c['PP'] in cat_pp_partida:
            res['PARTIDA'] = 'SI' if c['PARTIDA'] in cat_pp_partida[c['PP']] else 'NO'
            if res['PARTIDA'] == 'NO':
                cap = c['PARTIDA'][0] if c['PARTIDA'] else ''
                ps = sorted([p for p in cat_pp_partida[c['PP']] if p[0] == cap])[:10]
                sug['PARTIDA'] = ', '.join(ps) if ps else 'N/A'
        else:
            todas = set()
            for ps in cat_pp_partida.values(): todas.update(ps)
            res['PARTIDA'] = 'SI' if c['PARTIDA'] in todas else 'NO'
            if res['PARTIDA'] == 'NO': sug['PARTIDA'] = '(especifica PP)'
    # TG - desde catálogo C
    if c['TG']:
        if c['PARTIDA'] and c['PARTIDA'] in partida_tg:
            tgs_validos = sorted(partida_tg[c['PARTIDA']])
            res['TG'] = 'SI' if c['TG'] in tgs_validos else 'NO'
            if res['TG'] == 'NO': sug['TG'] = ', '.join(tgs_validos)
        else:
            res['TG'] = 'SI' if c['TG'] in all_tgs else 'NO'
            if res['TG'] == 'NO': sug['TG'] = ', '.join(sorted(all_tgs))
    # FF - desde catálogo C
    if c['FF']:
        if c['PARTIDA'] and c['TG'] and c['PARTIDA'] in tg_ff_por_partida:
            if c['TG'] in tg_ff_por_partida[c['PARTIDA']]:
                ffs_validos = sorted(tg_ff_por_partida[c['PARTIDA']][c['TG']])
                res['FF'] = 'SI' if c['FF'] in ffs_validos else 'NO'
                if res['FF'] == 'NO': sug['FF'] = ', '.join(ffs_validos)
            else:
                res['FF'] = 'NO'
                sug['FF'] = f'(TG {c["TG"]} no válido)'
        elif c['PARTIDA'] and c['PARTIDA'] in cat_estructura['partida_tg_ff']:
            ffs_validos = sorted(set(ff for tg, ff in cat_estructura['partida_tg_ff'][c['PARTIDA']]))
            res['FF'] = 'SI' if c['FF'] in ffs_validos else 'NO'
            if res['FF'] == 'NO': sug['FF'] = ', '.join(ffs_validos)
        else:
            res['FF'] = 'NO'
            sug['FF'] = '(especifica PARTIDA)'
    if c['EF']:
        res['EF'] = 'SI' if c['EF'] in EFS_VALIDOS else 'NO'
        if res['EF'] == 'NO': sug['EF'] = '00 a 34'
    if c['PPI'] and c['PPI'] != '00000000000':
        res['PPI'] = 'SI' if len(c['PPI']) == 11 else 'NO'
        if res['PPI'] == 'NO': sug['PPI'] = f'11 díg'
    if c['AUX2'] and c['AUX2'] != '00000':
        res['AUX2'] = 'SI' if len(c['AUX2']) == 5 else 'NO'
        if res['AUX2'] == 'NO': sug['AUX2'] = f'5 díg'
    if c['COP'] and c['COP'] != '00':
        res['COP'] = 'SI' if len(c['COP']) == 2 else 'NO'
        if res['COP'] == 'NO': sug['COP'] = f'2 díg'
    return res, sug, c

def procesar_archivo_pipp(archivo):
    df_raw = pd.read_excel(archivo, header=None, dtype=str)
    fila_datos = None
    for i in range(min(15, len(df_raw))):
        val0 = str(df_raw.iloc[i, 0]).strip() if pd.notna(df_raw.iloc[i, 0]) else ''
        val1 = str(df_raw.iloc[i, 1]).strip() if df_raw.shape[1] > 1 and pd.notna(df_raw.iloc[i, 1]) else ''
        if (val0.isdigit() and len(val0) <= 2 and val0 != '0') or (val1.isdigit() and len(val1) <= 2 and val1 != '0'):
            fila_datos = i
            break
    if fila_datos is None: return None, "No se detectó formato PIPP"
    df_datos = df_raw.iloc[fila_datos:].reset_index(drop=True)
    claves = []
    for _, row in df_datos.iterrows():
        if len(row) < 13: continue
        clave = {
            'RAMO': str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else '',
            'UR': str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else '',
            'AÑO': str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else '',
            'FIN': str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else '',
            'FUN': str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else '',
            'SF': str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else '',
            'RG': str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else '',
            'AI': str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else '',
            'PP': str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else '',
            'PARTIDA': str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else '',
            'TG': str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else '',
            'FF': str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else '',
            'EF': str(row.iloc[13]).strip() if len(row) > 13 and pd.notna(row.iloc[13]) else '',
            'PPI': str(row.iloc[14]).strip() if len(row) > 14 and pd.notna(row.iloc[14]) else '',
            'AUX2': str(row.iloc[15]).strip() if len(row) > 15 and pd.notna(row.iloc[15]) else '',
            'COP': str(row.iloc[16]).strip() if len(row) > 16 and pd.notna(row.iloc[16]) else '',
        }
        if clave['RAMO'] and clave['RAMO'].lower() != 'nan': claves.append(clave)
    return claves, f"Formato PIPP (fila {fila_datos + 1})"

def generar_excel_resultados(resultados):
    wb = Workbook()
    ws = wb.active
    ws.title = "Validación"
    si_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
    no_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
    header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center = Alignment(horizontal='center')
    campos = ['RAMO', 'UR', 'AÑO', 'FIN', 'FUN', 'SF', 'RG', 'AI', 'PP', 'PARTIDA', 'TG', 'FF', 'EF', 'PPI', 'AUX2', 'COP']
    headers = campos + ['VÁLIDO', 'ERRORES', 'SUGERENCIAS']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.border = border
    for i, r in enumerate(resultados, 2):
        for col, campo in enumerate(campos, 1):
            cell = ws.cell(row=i, column=col, value=r.get(campo, ''))
            cell.border = border
            cell.alignment = center
        cell = ws.cell(row=i, column=17, value=r['VÁLIDO'])
        cell.border = border
        cell.fill = si_fill if r['VÁLIDO'] == 'SI' else no_fill
        cell.font = Font(bold=True)
        ws.cell(row=i, column=18, value=r.get('ERRORES', '')).border = border
        ws.cell(row=i, column=19, value=r.get('SUGERENCIAS', '')).border = border
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# INTERFAZ
st.markdown("""
<div class="main-header">
    <h1>✓ Validador de Claves Presupuestarias PIPP 2026</h1>
    <p>Sistema de validación usando los 3 catálogos oficiales de SADER</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("###  Cargar Catálogos")
    st.markdown("---")
    archivo_pp = st.file_uploader("A. Pp-Partida Específica", type=['xlsx'], key="cat_a")
    archivo_rel = st.file_uploader("B. Ramo-Pp-Función-AI-UR", type=['xlsx'], key="cat_b")
    archivo_eco = st.file_uploader("C. Estructura Económica", type=['xlsx'], key="cat_c")
    st.markdown("---")
    cat_pp_partida = cargar_catalogo_pp_partida(archivo_pp) if archivo_pp else None
    cat_relaciones = cargar_catalogo_relaciones(archivo_rel) if archivo_rel else None
    cat_estructura = cargar_catalogo_estructura(archivo_eco) if archivo_eco else None
    st.markdown("###  Estadísticas")
    if cat_pp_partida:
        total_partidas = sum(len(v) for v in cat_pp_partida.values())
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(cat_pp_partida)}</div><div class="stat-label">Programas (Pp)</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-number">{total_partidas:,}</div><div class="stat-label">Partidas totales</div></div>', unsafe_allow_html=True)
    else: st.caption(" Catálogo A no cargado")
    if cat_relaciones:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(cat_relaciones["urs"])}</div><div class="stat-label">Unidades Responsables</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(cat_relaciones["ur_fin_fun_sf_ai_pp"]):,}</div><div class="stat-label">Combinaciones válidas</div></div>', unsafe_allow_html=True)
    else: st.caption(" Catálogo B no cargado")
    if cat_estructura:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(cat_estructura["partida_tg_ff"])}</div><div class="stat-label">Partidas con TG-FF</div></div>', unsafe_allow_html=True)
    else: st.caption(" Catálogo C no cargado")

hay_catalogos = cat_pp_partida or cat_relaciones or cat_estructura
todos_catalogos = cat_pp_partida and cat_relaciones and cat_estructura

if not hay_catalogos:
    st.info(" Carga al menos un catálogo en la barra lateral para comenzar")
    st.stop()

if todos_catalogos:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([" Validación Individual", " Validación Masiva", " Pp-Partida", " UR-FIN-FUN-SF-AI-PP", " Partida-TG-FF", " Explorar Catálogo"])
else:
    tabs_disponibles = []
    if cat_pp_partida: tabs_disponibles += [" Pp-Partida", "📖 Explorar Catálogo"]
    if cat_relaciones: tabs_disponibles.append(" UR-FIN-FUN-SF-AI-PP")
    if cat_estructura: tabs_disponibles.append(" Partida-TG-FF")
    if not tabs_disponibles: st.stop()
    tabs = st.tabs(tabs_disponibles)

# TAB 1: Validación Individual
if todos_catalogos:
    with tab1:
        st.markdown("### Validar clave (parcial o completa)")
        st.caption("Solo se validan los campos que ingreses.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ramo = st.text_input("RAMO", value="08", max_chars=2)
            fin = st.text_input("FIN", max_chars=1)
            ai = st.text_input("AI", max_chars=3)
            tg = st.text_input("TG", max_chars=1)
        with col2:
            ur = st.text_input("UR", max_chars=3)
            fun = st.text_input("FUN", max_chars=1)
            pp = st.text_input("PP", max_chars=4)
            ff = st.text_input("FF", max_chars=1)
        with col3:
            año = st.text_input("AÑO", value="2026", max_chars=4)
            sf = st.text_input("SF", max_chars=2)
            partida = st.text_input("PARTIDA", max_chars=5)
            ef = st.text_input("EF", max_chars=2)
        with col4:
            rg = st.text_input("RG", max_chars=2)
            ppi = st.text_input("PPI", max_chars=11)
            aux2 = st.text_input("AUX2", max_chars=5)
            cop = st.text_input("COP", max_chars=2)
        if st.button("✓ Validar", type="primary", key="validar_individual"):
            clave = {'RAMO': ramo, 'UR': ur, 'AÑO': año, 'FIN': fin, 'FUN': fun, 'SF': sf, 'RG': rg, 'AI': ai, 'PP': pp, 'PARTIDA': partida, 'TG': tg, 'FF': ff, 'EF': ef, 'PPI': ppi, 'AUX2': aux2, 'COP': cop}
            res, sug, c_norm = validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura)
            if not res: st.warning("Ingresa al menos un campo")
            else:
                total_ok = sum(1 for v in res.values() if v == 'SI')
                if total_ok == len(res): st.markdown(f'<div class="result-valid"><strong> VÁLIDO</strong> ({total_ok}/{len(res)})</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="result-invalid"><strong>❌ CON ERRORES</strong> ({total_ok}/{len(res)})</div>', unsafe_allow_html=True)
                st.markdown("#### Detalle")
                for campo in ['RAMO', 'UR', 'AÑO', 'FIN', 'FUN', 'SF', 'RG', 'AI', 'PP', 'PARTIDA', 'TG', 'FF', 'EF', 'PPI', 'AUX2', 'COP']:
                    if campo in res:
                        if res[campo] == 'SI': st.success(f" **{campo}** = `{c_norm.get(campo, '')}`")
                        else: st.error(f"❌ **{campo}** = `{c_norm.get(campo, '')}` → Válidos: {sug.get(campo, '')}")

# TAB 2: Validación Masiva
if todos_catalogos:
    with tab2:
        st.markdown("### Validar archivo completo")
        archivo_validar = st.file_uploader("Archivo PIPP", type=['xlsx', 'xls'], key="validar_masivo")
        if archivo_validar:
            claves, mensaje = procesar_archivo_pipp(archivo_validar)
            if claves is None: st.error(mensaje)
            else:
                st.info(f"📋 {mensaje} - **{len(claves)}** registros")
                if st.button("✓ Validar todos", type="primary"):
                    resultados = []
                    progress = st.progress(0)
                    for i, clave in enumerate(claves):
                        res, sug, c_norm = validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura)
                        errores = [k for k, v in res.items() if v == 'NO']
                        sugerencias_txt = '; '.join(f"{k}:{sug[k]}" for k in errores if k in sug)
                        resultados.append({**c_norm, 'VÁLIDO': 'SI' if not errores else 'NO', 'ERRORES': ', '.join(errores), 'SUGERENCIAS': sugerencias_txt})
                        progress.progress((i + 1) / len(claves))
                    validos = sum(1 for r in resultados if r['VÁLIDO'] == 'SI')
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total", len(resultados))
                    c2.metric("Válidos ✓", validos)
                    c3.metric("Errores ✗", len(resultados) - validos)
                    df_res = pd.DataFrame(resultados)
                    st.dataframe(df_res.style.apply(lambda row: ['background-color: #E8F5E9' if row['VÁLIDO'] == 'SI' else 'background-color: #FFEBEE'] * len(row), axis=1), use_container_width=True, height=400)
                    st.download_button(" Descargar", generar_excel_resultados(resultados), "Validacion.xlsx")

# TAB 3: Pp-Partida
tab_pp = tab3 if todos_catalogos else (tabs[0] if cat_pp_partida else None)
if tab_pp and cat_pp_partida:
    with tab_pp:
        st.markdown("### Validador Pp - Partida")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: pp_input = st.text_input("Pp", max_chars=4, key="pp_a").upper().strip()
        with c2: partida_input = st.text_input("Partida (opcional)", max_chars=5, key="partida_a").strip()
        with c3: st.markdown("<br>", unsafe_allow_html=True); buscar_pp = st.button("Buscar", key="buscar_pp")
        if buscar_pp and pp_input:
            partida_check = partida_input.zfill(5) if partida_input else ""
            if pp_input not in cat_pp_partida: st.error(f" Pp **{pp_input}** no existe")
            elif not partida_check or partida_check == "00000":
                partidas = sorted(cat_pp_partida[pp_input])
                st.success(f" **{pp_input}** tiene **{len(partidas)}** partidas")
                caps = {}
                for p in partidas: caps.setdefault(p[0], []).append(p)
                for cap in sorted(caps.keys()):
                    with st.expander(f"Cap {cap}000 - {NOMBRE_CAPITULO.get(cap, '')} ({len(caps[cap])})"): st.code(", ".join(caps[cap]))
            elif partida_check in cat_pp_partida[pp_input]: st.markdown(f'<div class="result-valid"><strong>✅ VÁLIDO</strong></div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="result-invalid"><strong>❌ NO VÁLIDO</strong></div>', unsafe_allow_html=True)

# TAB 4: UR-FIN-FUN-SF-AI-PP
tab_rel = tab4 if todos_catalogos else (tabs[2] if cat_pp_partida and cat_relaciones else (tabs[0] if cat_relaciones and not cat_pp_partida else None))
if tab_rel and cat_relaciones:
    with tab_rel:
        st.markdown("### Validador UR-FIN-FUN-SF-AI-PP")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: ur_b = st.text_input("UR", max_chars=3, key="ur_b").upper().strip()
        with c2: fin_b = st.text_input("FIN", max_chars=1, key="fin_b").strip()
        with c3: fun_b = st.text_input("FUN", max_chars=1, key="fun_b").strip()
        with c4: sf_b = st.text_input("SF", max_chars=2, key="sf_b").strip()
        with c5: ai_b = st.text_input("AI", max_chars=3, key="ai_b").strip()
        with c6: pp_b = st.text_input("PP", max_chars=4, key="pp_b").upper().strip()
        if st.button("Validar", key="validar_b"):
            sf_n, ai_n = normalizar(sf_b, 2), normalizar(ai_b, 3)
            cat_urs = cat_relaciones['urs']
            resultados_b = []
            if ur_b: resultados_b.append(('UR', ur_b, 'SI' if ur_b in cat_urs else 'NO', sorted(cat_urs)[:15] if ur_b not in cat_urs else None))
            if not resultados_b: st.warning("Ingresa al menos un campo")
            else:
                errores = [r for r in resultados_b if r[2] == 'NO']
                st.markdown('<div class="result-valid"><strong> VÁLIDO</strong></div>' if not errores else '<div class="result-invalid"><strong>❌ CON ERRORES</strong></div>', unsafe_allow_html=True)
                for campo, valor, estado, validos in resultados_b:
                    if estado == 'SI': st.success(f" **{campo}** = `{valor}`")
                    else: st.error(f" **{campo}** = `{valor}` → Válidos: {', '.join(validos[:15]) if validos else 'N/A'}")

# TAB 5: Partida-TG-FF
tab_eco = tab5 if todos_catalogos else (tabs[-1] if cat_estructura else None)
if tab_eco and cat_estructura:
    with tab_eco:
        st.markdown("### Validador Partida-TG-FF")
        st.caption("Combinaciones TG-FF del catálogo de Estructura Económica")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1: partida_c = st.text_input("Partida", max_chars=5, key="partida_c").strip()
        with c2: tg_c = st.text_input("TG", max_chars=1, key="tg_c").strip()
        with c3: ff_c = st.text_input("FF", max_chars=1, key="ff_c").strip()
        with c4: st.markdown("<br>", unsafe_allow_html=True); validar_c = st.button("Validar", key="validar_c")
        partida_tg_ff = cat_estructura['partida_tg_ff']
        partida_tg = cat_estructura['partida_tg']
        tg_ff_por_partida = cat_estructura['tg_ff_por_partida']
        if validar_c:
            partida_n = normalizar(partida_c, 5) if partida_c else ""
            if not partida_n and not tg_c: st.warning("Ingresa Partida o TG")
            elif partida_n and partida_n not in partida_tg_ff: st.error(f"❌ Partida **{partida_n}** no existe")
            elif partida_n and not tg_c:
                combos = sorted(partida_tg_ff[partida_n])
                st.success(f" **{partida_n}** tiene {len(combos)} combos TG-FF:")
                for tg, ff in combos: st.code(f"TG={tg}, FF={ff}")
            elif partida_n and tg_c and not ff_c:
                if tg_c in tg_ff_por_partida.get(partida_n, {}): st.success(f"TG={tg_c} → FF válidos: {', '.join(sorted(tg_ff_por_partida[partida_n][tg_c]))}")
                else: st.error(f" TG **{tg_c}** no válido. Válidos: {', '.join(sorted(partida_tg.get(partida_n, set())))}")
            elif partida_n and tg_c and ff_c:
                if tg_c in tg_ff_por_partida.get(partida_n, {}) and ff_c in tg_ff_por_partida[partida_n][tg_c]: st.markdown('<div class="result-valid"><strong>✅ VÁLIDO</strong></div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="result-invalid"><strong>❌ NO VÁLIDO</strong></div>', unsafe_allow_html=True)

# TAB 6: Explorar
tab_explorar = tab6 if todos_catalogos else (tabs[1] if cat_pp_partida else None)
if tab_explorar and cat_pp_partida:
    with tab_explorar:
        st.markdown("### Explorar catálogo")
        pp_sel = st.selectbox("Programa", [""] + sorted(cat_pp_partida.keys()), format_func=lambda x: f"{x} ({len(cat_pp_partida.get(x, []))})" if x else "-- Seleccionar --")
        if pp_sel:
            partidas = sorted(cat_pp_partida[pp_sel])
            st.success(f"**{pp_sel}**: {len(partidas)} partidas")
            caps = {}
            for p in partidas: caps.setdefault(p[0], []).append(p)
            for cap in sorted(caps.keys()):
                with st.expander(f"**Cap {cap}000** - {NOMBRE_CAPITULO.get(cap, '')} ({len(caps[cap])})", expanded=True):
                    cols = st.columns(6)
                    for i, p in enumerate(caps[cap]): cols[i % 6].code(p)

st.markdown("---")
st.caption("Validador PIPP 2026 | SADER")
