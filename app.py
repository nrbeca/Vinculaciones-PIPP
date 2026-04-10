"""
Validador de Claves Presupuestarias PIPP 2026
Aplicación completa para validar combinaciones usando los 3 catálogos oficiales.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Validador PIPP 2026 | SADER",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS CSS
# ══════════════════════════════════════════════════════════════════════════════

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
    
    .stat-card.success { border-left-color: var(--verde-ok); }
    .stat-card.error { border-left-color: var(--rojo-error); }
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
    
    .stButton > button:hover {
        background: var(--guinda-claro);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Combinaciones TG-FF válidas (hardcodeadas)
COMBOS_TG_FF = {
    '1': ['1', '4', '5', '6'],
    '2': ['1', '4', '5', '6'],
    '3': ['1', '4'],
    '7': ['1', '4', '6'],
    '8': ['1', '4', '6'],
}

# EFs válidos (00 a 34)
EFS_VALIDOS = ['00'] + [str(i).zfill(2) for i in range(1, 35)]

# RGs válidos
RGS_VALIDOS = ['00', '01', '02', '03']

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

def normalizar(valor, digitos=None):
    """Normaliza un valor: limpia y agrega ceros si es necesario."""
    if valor is None:
        return ''
    valor = str(valor).strip()
    if valor.lower() in ['nan', 'none', '']:
        return ''
    if digitos and valor.isdigit():
        return valor.zfill(digitos)
    return valor


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CARGA DE CATÁLOGOS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def cargar_catalogo_pp_partida(archivo):
    """Carga catálogo A: Pp-Partida Específica."""
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    
    partidas_por_pp = {}
    
    for _, row in df.iterrows():
        mod = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        prog = normalizar(row.iloc[4], 3)
        partida = normalizar(row.iloc[6], 5)
        
        if mod and prog and partida:
            pp = f"{mod}{prog}"
            if pp not in partidas_por_pp:
                partidas_por_pp[pp] = set()
            partidas_por_pp[pp].add(partida)
    
    return partidas_por_pp


@st.cache_data
def cargar_catalogo_relaciones(archivo):
    """Carga catálogo B: Ramo-Pp-Función-AI-UR."""
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    
    cat_urs = set()
    cat_ur_fin = set()
    cat_ur_fin_fun = set()
    cat_ur_fin_fun_sf = set()
    cat_ur_fin_fun_sf_ai = set()
    cat_ur_fin_fun_sf_ai_pp = set()
    
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
                            if pp:
                                cat_ur_fin_fun_sf_ai_pp.add((ur, fin, fun, sf, ai, pp))
    
    return {
        'urs': cat_urs,
        'ur_fin': cat_ur_fin,
        'ur_fin_fun': cat_ur_fin_fun,
        'ur_fin_fun_sf': cat_ur_fin_fun_sf,
        'ur_fin_fun_sf_ai': cat_ur_fin_fun_sf_ai,
        'ur_fin_fun_sf_ai_pp': cat_ur_fin_fun_sf_ai_pp
    }


@st.cache_data
def cargar_catalogo_estructura(archivo):
    """Carga catálogo C: Estructura Económica."""
    df = pd.read_excel(archivo, header=None, dtype=str)
    df = df.iloc[1:].reset_index(drop=True)
    
    partida_tg_ff = {}
    
    for _, row in df.iterrows():
        partida = normalizar(row.iloc[2], 5)
        tg = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        ff = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
        
        if partida and tg and ff:
            if partida not in partida_tg_ff:
                partida_tg_ff[partida] = set()
            partida_tg_ff[partida].add((tg, ff))
    
    return partida_tg_ff


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE VALIDACIÓN COMPLETA
# ══════════════════════════════════════════════════════════════════════════════

def validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura):
    """Valida una clave completa contra los 3 catálogos."""
    
    # Normalizar valores
    c = {
        'RAMO': normalizar(clave.get('RAMO'), 2),
        'UR': normalizar(clave.get('UR')),
        'AÑO': normalizar(clave.get('AÑO')),
        'FIN': normalizar(clave.get('FIN')),
        'FUN': normalizar(clave.get('FUN')),
        'SF': normalizar(clave.get('SF'), 2),
        'RG': normalizar(clave.get('RG'), 2),
        'AI': normalizar(clave.get('AI'), 3),
        'PP': normalizar(clave.get('PP')).upper(),
        'PARTIDA': normalizar(clave.get('PARTIDA'), 5),
        'TG': normalizar(clave.get('TG')),
        'FF': normalizar(clave.get('FF')),
        'EF': normalizar(clave.get('EF'), 2),
        'PPI': normalizar(clave.get('PPI')),
        'AUX2': normalizar(clave.get('AUX2'), 5),
        'COP': normalizar(clave.get('COP'), 2),
    }
    
    res = {}
    sug = {}
    
    # Extraer sets del catálogo de relaciones
    cat_urs = cat_relaciones['urs']
    cat_ur_fin = cat_relaciones['ur_fin']
    cat_ur_fin_fun = cat_relaciones['ur_fin_fun']
    cat_ur_fin_fun_sf = cat_relaciones['ur_fin_fun_sf']
    cat_ur_fin_fun_sf_ai = cat_relaciones['ur_fin_fun_sf_ai']
    cat_ur_fin_fun_sf_ai_pp = cat_relaciones['ur_fin_fun_sf_ai_pp']
    
    # 1. RAMO
    res['RAMO'] = 'SI' if c['RAMO'] == '08' else 'NO'
    if res['RAMO'] == 'NO':
        sug['RAMO'] = '08'
    
    # 2. UR
    res['UR'] = 'SI' if c['UR'] in cat_urs else 'NO'
    if res['UR'] == 'NO':
        sug['UR'] = ', '.join(sorted(cat_urs)[:15])
    
    # 3. AÑO
    res['AÑO'] = 'SI' if c['AÑO'] == '2026' else 'NO'
    if res['AÑO'] == 'NO':
        sug['AÑO'] = '2026'
    
    # 4. FIN
    if c['UR'] in cat_urs:
        fins_v = sorted(set(f for u, f in cat_ur_fin if u == c['UR']))
        res['FIN'] = 'SI' if c['FIN'] in fins_v else 'NO'
        if res['FIN'] == 'NO':
            sug['FIN'] = ', '.join(fins_v)
    else:
        res['FIN'] = 'NO'
        sug['FIN'] = '(corrige UR)'
    
    # 5. FUN
    if res.get('FIN') == 'SI':
        funs_v = sorted(set(f for u, fi, f in cat_ur_fin_fun if u == c['UR'] and fi == c['FIN']))
        res['FUN'] = 'SI' if c['FUN'] in funs_v else 'NO'
        if res['FUN'] == 'NO':
            sug['FUN'] = ', '.join(funs_v)
    else:
        res['FUN'] = 'NO'
        sug['FUN'] = '(corrige FIN)'
    
    # 6. SF
    if res.get('FUN') == 'SI':
        sfs_v = sorted(set(s for u, fi, fu, s in cat_ur_fin_fun_sf if u == c['UR'] and fi == c['FIN'] and fu == c['FUN']))
        res['SF'] = 'SI' if c['SF'] in sfs_v else 'NO'
        if res['SF'] == 'NO':
            sug['SF'] = ', '.join(sfs_v)
    else:
        res['SF'] = 'NO'
        sug['SF'] = '(corrige FUN)'
    
    # 7. RG
    res['RG'] = 'SI' if c['RG'] in RGS_VALIDOS else 'NO'
    if res['RG'] == 'NO':
        sug['RG'] = ', '.join(RGS_VALIDOS)
    
    # 8. AI
    if res.get('SF') == 'SI':
        ais_v = sorted(set(a for u, fi, fu, s, a in cat_ur_fin_fun_sf_ai if u == c['UR'] and fi == c['FIN'] and fu == c['FUN'] and s == c['SF']))
        res['AI'] = 'SI' if c['AI'] in ais_v else 'NO'
        if res['AI'] == 'NO':
            sug['AI'] = ', '.join(ais_v)
    else:
        res['AI'] = 'NO'
        sug['AI'] = '(corrige SF)'
    
    # 9. PP
    if res.get('AI') == 'SI':
        pps_v = sorted(set(p for u, fi, fu, s, a, p in cat_ur_fin_fun_sf_ai_pp if u == c['UR'] and fi == c['FIN'] and fu == c['FUN'] and s == c['SF'] and a == c['AI']))
        res['PP'] = 'SI' if c['PP'] in pps_v else 'NO'
        if res['PP'] == 'NO':
            sug['PP'] = ', '.join(pps_v)
    else:
        res['PP'] = 'NO'
        sug['PP'] = '(corrige AI)'
    
    # 10. PARTIDA
    if c['PP'] in cat_pp_partida:
        res['PARTIDA'] = 'SI' if c['PARTIDA'] in cat_pp_partida[c['PP']] else 'NO'
        if res['PARTIDA'] == 'NO':
            cap = c['PARTIDA'][0] if c['PARTIDA'] else ''
            ps = sorted([p for p in cat_pp_partida[c['PP']] if p[0] == cap])[:10]
            sug['PARTIDA'] = ', '.join(ps) if ps else 'N/A'
    else:
        res['PARTIDA'] = 'NO'
        sug['PARTIDA'] = '(corrige PP)'
    
    # 11. TG
    res['TG'] = 'SI' if c['TG'] in COMBOS_TG_FF else 'NO'
    if res['TG'] == 'NO':
        sug['TG'] = ', '.join(sorted(COMBOS_TG_FF.keys()))
    
    # 12. FF
    if res.get('TG') == 'SI':
        ffs_v = COMBOS_TG_FF.get(c['TG'], [])
        res['FF'] = 'SI' if c['FF'] in ffs_v else 'NO'
        if res['FF'] == 'NO':
            sug['FF'] = ', '.join(ffs_v)
    else:
        res['FF'] = 'NO'
        sug['FF'] = '(corrige TG)'
    
    # 13. EF
    res['EF'] = 'SI' if c['EF'] in EFS_VALIDOS else 'NO'
    if res['EF'] == 'NO':
        sug['EF'] = '00 a 34'
    
    # 14. PPI
    res['PPI'] = 'SI' if c['PPI'] == '' or len(c['PPI']) == 11 else 'NO'
    if res['PPI'] == 'NO':
        sug['PPI'] = f'11 dígitos (tiene {len(c["PPI"])})'
    
    # 15. AUX2
    res['AUX2'] = 'SI' if c['AUX2'] == '' or len(c['AUX2']) == 5 else 'NO'
    if res['AUX2'] == 'NO':
        sug['AUX2'] = f'5 dígitos (tiene {len(c["AUX2"])})'
    
    # 16. COP
    res['COP'] = 'SI' if c['COP'] == '' or len(c['COP']) == 2 else 'NO'
    if res['COP'] == 'NO':
        sug['COP'] = f'2 dígitos (tiene {len(c["COP"])})'
    
    return res, sug, c


def procesar_archivo_pipp(archivo):
    """Procesa un archivo en formato PIPP y extrae las claves."""
    df_raw = pd.read_excel(archivo, header=None, dtype=str)
    
    # Detectar fila de datos
    fila_datos = None
    for i in range(min(15, len(df_raw))):
        val0 = str(df_raw.iloc[i, 0]).strip() if pd.notna(df_raw.iloc[i, 0]) else ''
        val1 = str(df_raw.iloc[i, 1]).strip() if df_raw.shape[1] > 1 and pd.notna(df_raw.iloc[i, 1]) else ''
        
        if (val0.isdigit() and len(val0) <= 2 and val0 != '0') or (val1.isdigit() and len(val1) <= 2 and val1 != '0'):
            fila_datos = i
            break
    
    if fila_datos is None:
        return None, "No se detectó formato PIPP"
    
    df_datos = df_raw.iloc[fila_datos:].reset_index(drop=True)
    claves = []
    
    for _, row in df_datos.iterrows():
        if len(row) < 13:
            continue
        
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
        
        if clave['RAMO'] and clave['RAMO'].lower() != 'nan':
            claves.append(clave)
    
    return claves, f"Formato PIPP detectado (fila {fila_datos + 1})"


def generar_excel_resultados(resultados):
    """Genera archivo Excel con resultados de validación."""
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


# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="main-header">
    <h1>✓ Validador de Claves Presupuestarias PIPP 2026</h1>
    <p>Sistema de validación usando los 3 catálogos oficiales de SADER</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Carga de catálogos
with st.sidebar:
    st.markdown("###  Cargar Catálogos")
    st.caption("Sube los 3 catálogos para habilitar todas las funciones")
    
    st.markdown("---")
    
    # Catálogo A
    st.markdown("**A. Pp - Partida Específica**")
    archivo_pp = st.file_uploader("Pp_-_Partida_Especifica_2026.xlsx", type=['xlsx'], key="cat_a")
    
    # Catálogo B
    st.markdown("**B. Ramo-Pp-Función-AI-UR**")
    archivo_rel = st.file_uploader("Ramo_-_Pp_-_Funcion_-_AI_-_UR_2026.xlsx", type=['xlsx'], key="cat_b")
    
    # Catálogo C
    st.markdown("**C. Estructura Económica**")
    archivo_eco = st.file_uploader("Ramo_Estructura_Economica_2026.xlsx", type=['xlsx'], key="cat_c")
    
    st.markdown("---")
    
    # Estado de catálogos
    st.markdown("###  Estado")
    
    cat_pp_partida = None
    cat_relaciones = None
    cat_estructura = None
    
    if archivo_pp:
        cat_pp_partida = cargar_catalogo_pp_partida(archivo_pp)
        st.success(f" A: {len(cat_pp_partida)} Pps")
    else:
        st.warning(" A: No cargado")
    
    if archivo_rel:
        cat_relaciones = cargar_catalogo_relaciones(archivo_rel)
        st.success(f" B: {len(cat_relaciones['ur_fin_fun_sf_ai_pp'])} combos")
    else:
        st.warning(" B: No cargado")
    
    if archivo_eco:
        cat_estructura = cargar_catalogo_estructura(archivo_eco)
        st.success(f" C: {len(cat_estructura)} partidas")
    else:
        st.warning(" C: No cargado")

# Verificar si hay catálogos cargados
hay_catalogos = cat_pp_partida or cat_relaciones or cat_estructura
todos_catalogos = cat_pp_partida and cat_relaciones and cat_estructura

if not hay_catalogos:
    st.info(" Carga al menos un catálogo en la barra lateral para comenzar")
    st.stop()

# Tabs principales
if todos_catalogos:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        " Validación Individual",
        " Validación Masiva",
        " Pp-Partida",
        " UR-FIN-FUN-SF-AI-PP",
        " Partida-TG-FF"
    ])
else:
    tabs_disponibles = []
    if cat_pp_partida:
        tabs_disponibles.append(" Pp-Partida")
    if cat_relaciones:
        tabs_disponibles.append(" UR-FIN-FUN-SF-AI-PP")
    if cat_estructura:
        tabs_disponibles.append(" Partida-TG-FF")
    
    if not tabs_disponibles:
        st.stop()
    
    tabs = st.tabs(tabs_disponibles)
    tab_idx = 0

# ══════════════════════════════════════════════════════════════════════════════
# TAB: VALIDACIÓN INDIVIDUAL (requiere los 3 catálogos)
# ══════════════════════════════════════════════════════════════════════════════

if todos_catalogos:
    with tab1:
        st.markdown("### Validar una clave completa")
        st.caption("Ingresa los 16 campos de la clave presupuestaria")
        
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
            rg = st.text_input("RG", value="00", max_chars=2)
            ppi = st.text_input("PPI", value="00000000000", max_chars=11)
            aux2 = st.text_input("AUX2", value="00000", max_chars=5)
            cop = st.text_input("COP", value="00", max_chars=2)
        
        if st.button("✓ Validar clave", type="primary"):
            clave = {
                'RAMO': ramo, 'UR': ur, 'AÑO': año, 'FIN': fin, 'FUN': fun,
                'SF': sf, 'RG': rg, 'AI': ai, 'PP': pp, 'PARTIDA': partida,
                'TG': tg, 'FF': ff, 'EF': ef, 'PPI': ppi, 'AUX2': aux2, 'COP': cop
            }
            
            res, sug, c_norm = validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura)
            
            # Mostrar resultados
            total_ok = sum(1 for v in res.values() if v == 'SI')
            total = len(res)
            
            if total_ok == total:
                st.markdown("""
                <div class="result-valid">
                    <strong> CLAVE VÁLIDA</strong><br>
                    Todos los campos son correctos
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-invalid">
                    <strong> CLAVE CON ERRORES</strong><br>
                    {total_ok}/{total} campos correctos
                </div>
                """, unsafe_allow_html=True)
            
            # Detalle por campo
            st.markdown("#### Detalle por campo")
            
            campos = ['RAMO', 'UR', 'AÑO', 'FIN', 'FUN', 'SF', 'RG', 'AI', 'PP', 'PARTIDA', 'TG', 'FF', 'EF', 'PPI', 'AUX2', 'COP']
            
            for campo in campos:
                estado = res.get(campo, '?')
                valor = c_norm.get(campo, '')
                
                if estado == 'SI':
                    st.success(f" **{campo}** = `{valor}`")
                else:
                    sugerencia = sug.get(campo, '')
                    st.error(f" **{campo}** = `{valor}` → Válidos: {sugerencia}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB: VALIDACIÓN MASIVA (requiere los 3 catálogos)
# ══════════════════════════════════════════════════════════════════════════════

if todos_catalogos:
    with tab2:
        st.markdown("### Validar archivo completo")
        st.caption("Sube un archivo en formato PIPP para validar múltiples claves")
        
        archivo_validar = st.file_uploader("Archivo con claves a validar", type=['xlsx', 'xls'], key="validar_masivo")
        
        if archivo_validar:
            claves, mensaje = procesar_archivo_pipp(archivo_validar)
            
            if claves is None:
                st.error(mensaje)
            else:
                st.info(f" {mensaje} - **{len(claves)}** registros encontrados")
                
                if st.button("✓ Validar todos", type="primary"):
                    resultados = []
                    
                    progress = st.progress(0)
                    for i, clave in enumerate(claves):
                        res, sug, c_norm = validar_clave_completa(clave, cat_pp_partida, cat_relaciones, cat_estructura)
                        
                        errores = [k for k, v in res.items() if v == 'NO']
                        sugerencias_txt = '; '.join(f"{k}:{sug[k]}" for k in errores if k in sug)
                        
                        resultados.append({
                            **c_norm,
                            'VÁLIDO': 'SI' if not errores else 'NO',
                            'ERRORES': ', '.join(errores),
                            'SUGERENCIAS': sugerencias_txt
                        })
                        
                        progress.progress((i + 1) / len(claves))
                    
                    # Estadísticas
                    validos = sum(1 for r in resultados if r['VÁLIDO'] == 'SI')
                    invalidos = len(resultados) - validos
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{len(resultados)}</div>
                            <div class="stat-label">Total registros</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stat-card success">
                            <div class="stat-number" style="color: #2E7D32">{validos}</div>
                            <div class="stat-label">Válidos ✓</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stat-card error">
                            <div class="stat-number" style="color: #C62828">{invalidos}</div>
                            <div class="stat-label">Con errores ✗</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Resumen por campo
                    st.markdown("#### Resumen por campo")
                    campos = ['RAMO', 'UR', 'AÑO', 'FIN', 'FUN', 'SF', 'RG', 'AI', 'PP', 'PARTIDA', 'TG', 'FF', 'EF']
                    
                    cols = st.columns(len(campos))
                    for i, campo in enumerate(campos):
                        errores_campo = sum(1 for r in resultados if campo in r.get('ERRORES', ''))
                        color = "#2E7D32" if errores_campo == 0 else "#C62828"
                        cols[i].markdown(f"**{campo}**<br><span style='color:{color}'>{len(resultados)-errores_campo}/{len(resultados)}</span>", unsafe_allow_html=True)
                    
                    # Tabla de resultados
                    st.markdown("---")
                    st.markdown("#### Detalle")
                    
                    df_resultados = pd.DataFrame(resultados)
                    
                    def highlight_valid(row):
                        if row['VÁLIDO'] == 'SI':
                            return ['background-color: #E8F5E9'] * len(row)
                        return ['background-color: #FFEBEE'] * len(row)
                    
                    st.dataframe(
                        df_resultados.style.apply(highlight_valid, axis=1),
                        use_container_width=True,
                        height=400
                    )
                    
                    # Descarga
                    excel_output = generar_excel_resultados(resultados)
                    st.download_button(
                        label=" Descargar resultados (.xlsx)",
                        data=excel_output,
                        file_name="Validacion_Completa.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB: Pp-Partida
# ══════════════════════════════════════════════════════════════════════════════

if todos_catalogos:
    tab_pp = tab3
elif cat_pp_partida:
    tab_pp = tabs[tab_idx]
    tab_idx += 1
else:
    tab_pp = None

if tab_pp and cat_pp_partida:
    with tab_pp:
        st.markdown("### Validador Pp - Partida")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            pp_input = st.text_input("Programa Presupuestario (Pp)", placeholder="Ej: K017, S263", max_chars=10, key="pp_a").upper().strip()
        
        with col2:
            partida_input = st.text_input("Partida (opcional)", placeholder="Ej: 52301", max_chars=5, key="partida_a").strip()
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_pp = st.button("Buscar", key="buscar_pp")
        
        if buscar_pp and pp_input:
            partida_check = partida_input.zfill(5) if partida_input else ""
            
            if pp_input not in cat_pp_partida:
                st.error(f" Pp **{pp_input}** no existe")
                similares = sorted(cat_pp_partida.keys())[:10]
                st.caption(f"Disponibles: {', '.join(similares)}")
            
            elif not partida_check or partida_check == "00000":
                partidas = sorted(cat_pp_partida[pp_input])
                st.success(f" Pp **{pp_input}** tiene **{len(partidas)}** partidas válidas")
                
                caps = {}
                for p in partidas:
                    cap = p[0]
                    if cap not in caps:
                        caps[cap] = []
                    caps[cap].append(p)
                
                for cap in sorted(caps.keys()):
                    with st.expander(f"Capítulo {cap}000 ({len(caps[cap])} partidas)"):
                        st.code(", ".join(caps[cap]))
            
            elif partida_check in cat_pp_partida[pp_input]:
                st.markdown(f"""
                <div class="result-valid">
                    <strong> VÁLIDO</strong><br>
                    Partida <code>{partida_check}</code> corresponde a Pp <code>{pp_input}</code>
                </div>
                """, unsafe_allow_html=True)
            
            else:
                st.markdown(f"""
                <div class="result-invalid">
                    <strong> NO VÁLIDO</strong><br>
                    Partida <code>{partida_check}</code> NO corresponde a Pp <code>{pp_input}</code>
                </div>
                """, unsafe_allow_html=True)
                
                cap = partida_check[0]
                similares = sorted([p for p in cat_pp_partida[pp_input] if p[0] == cap])
                if similares:
                    st.caption(f"Partidas válidas cap {cap}000: {', '.join(similares[:15])}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB: UR-FIN-FUN-SF-AI-PP
# ══════════════════════════════════════════════════════════════════════════════

if todos_catalogos:
    tab_rel = tab4
elif cat_relaciones:
    tab_rel = tabs[tab_idx]
    tab_idx += 1
else:
    tab_rel = None

if tab_rel and cat_relaciones:
    with tab_rel:
        st.markdown("### Validador UR-FIN-FUN-SF-AI-PP")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            ur_b = st.text_input("UR", max_chars=3, key="ur_b").upper().strip()
        with col2:
            fin_b = st.text_input("FIN", max_chars=1, key="fin_b").strip()
        with col3:
            fun_b = st.text_input("FUN", max_chars=1, key="fun_b").strip()
        with col4:
            sf_b = st.text_input("SF", max_chars=2, key="sf_b").strip()
        with col5:
            ai_b = st.text_input("AI", max_chars=3, key="ai_b").strip()
        with col6:
            pp_b = st.text_input("PP", max_chars=4, key="pp_b").upper().strip()
        
        if st.button("Validar combinación", key="validar_b"):
            cat_urs = cat_relaciones['urs']
            cat_ur_fin = cat_relaciones['ur_fin']
            cat_ur_fin_fun = cat_relaciones['ur_fin_fun']
            cat_ur_fin_fun_sf = cat_relaciones['ur_fin_fun_sf']
            cat_ur_fin_fun_sf_ai = cat_relaciones['ur_fin_fun_sf_ai']
            cat_ur_fin_fun_sf_ai_pp = cat_relaciones['ur_fin_fun_sf_ai_pp']
            
            sf_n = normalizar(sf_b, 2)
            ai_n = normalizar(ai_b, 3)
            
            errores = []
            
            if ur_b not in cat_urs:
                errores.append(('UR', ur_b, sorted(cat_urs)[:15]))
            else:
                fins_v = sorted(set(f for u, f in cat_ur_fin if u == ur_b))
                if fin_b not in fins_v:
                    errores.append(('FIN', fin_b, fins_v))
                else:
                    funs_v = sorted(set(f for u, fi, f in cat_ur_fin_fun if u == ur_b and fi == fin_b))
                    if fun_b not in funs_v:
                        errores.append(('FUN', fun_b, funs_v))
                    else:
                        sfs_v = sorted(set(s for u, fi, fu, s in cat_ur_fin_fun_sf if u == ur_b and fi == fin_b and fu == fun_b))
                        if sf_n not in sfs_v:
                            errores.append(('SF', sf_n, sfs_v))
                        else:
                            ais_v = sorted(set(a for u, fi, fu, s, a in cat_ur_fin_fun_sf_ai if u == ur_b and fi == fin_b and fu == fun_b and s == sf_n))
                            if ai_n not in ais_v:
                                errores.append(('AI', ai_n, ais_v))
                            else:
                                pps_v = sorted(set(p for u, fi, fu, s, a, p in cat_ur_fin_fun_sf_ai_pp if u == ur_b and fi == fin_b and fu == fun_b and s == sf_n and a == ai_n))
                                if pp_b not in pps_v:
                                    errores.append(('PP', pp_b, pps_v))
            
            if not errores:
                st.markdown("""
                <div class="result-valid">
                    <strong> COMBINACIÓN VÁLIDA</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-invalid">
                    <strong> COMBINACIÓN INVÁLIDA</strong>
                </div>
                """, unsafe_allow_html=True)
                
                for campo, valor, validos in errores:
                    st.error(f"**{campo}** = `{valor}` → Válidos: {', '.join(str(v) for v in validos[:15])}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB: Partida-TG-FF
# ══════════════════════════════════════════════════════════════════════════════

if todos_catalogos:
    tab_eco = tab5
elif cat_estructura:
    tab_eco = tabs[tab_idx]
    tab_idx += 1
else:
    tab_eco = None

if tab_eco and cat_estructura:
    with tab_eco:
        st.markdown("### Validador Partida-TG-FF")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            partida_c = st.text_input("Partida", max_chars=5, key="partida_c").strip()
        with col2:
            tg_c = st.text_input("TG", max_chars=1, key="tg_c").strip()
        with col3:
            ff_c = st.text_input("FF", max_chars=1, key="ff_c").strip()
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            validar_c = st.button("Validar", key="validar_c")
        
        if validar_c and partida_c:
            partida_n = normalizar(partida_c, 5)
            
            if partida_n not in cat_estructura:
                st.error(f" Partida **{partida_n}** no existe en el catálogo")
                cap = partida_n[0] if partida_n else ''
                similares = sorted([p for p in cat_estructura.keys() if p[0] == cap])[:15]
                if similares:
                    st.caption(f"Partidas cap {cap}000: {', '.join(similares)}")
            
            elif not tg_c:
                combos = sorted(cat_estructura[partida_n])
                st.success(f" Partida **{partida_n}** tiene {len(combos)} combinaciones TG-FF:")
                for tg, ff in combos:
                    st.code(f"TG={tg}, FF={ff}")
            
            else:
                # Validar TG primero con combos hardcodeados
                if tg_c not in COMBOS_TG_FF:
                    st.error(f" TG **{tg_c}** no es válido → Válidos: {', '.join(sorted(COMBOS_TG_FF.keys()))}")
                elif not ff_c:
                    ffs_v = COMBOS_TG_FF[tg_c]
                    st.info(f"TG={tg_c} → FF válidos: {', '.join(ffs_v)}")
                elif ff_c not in COMBOS_TG_FF[tg_c]:
                    st.error(f"❌ FF **{ff_c}** no es válido para TG={tg_c} → Válidos: {', '.join(COMBOS_TG_FF[tg_c])}")
                else:
                    st.markdown(f"""
                    <div class="result-valid">
                        <strong> VÁLIDO</strong><br>
                        TG={tg_c}, FF={ff_c} es una combinación válida
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("Validador PIPP 2026 | SADER - Secretaría de Agricultura y Desarrollo Rural")
