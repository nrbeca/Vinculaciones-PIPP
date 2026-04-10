# Validador de Claves Presupuestarias PIPP 2026

Sistema de validación de claves presupuestarias usando los 3 catálogos oficiales de SADER.

## 🚀 Funcionalidades

### Validadores individuales:
- **Pp-Partida**: Valida si una partida corresponde a un programa presupuestario
- **UR-FIN-FUN-SF-AI-PP**: Valida combinaciones de la estructura programática
- **Partida-TG-FF**: Valida combinaciones de tipo de gasto y fuente de financiamiento

### Validador completo:
- Valida los 16 campos de la clave presupuestaria
- Validación masiva desde archivo PIPP
- Exportación de resultados a Excel con sugerencias

## 📋 Campos validados

| Campo | Dígitos | Validación |
|-------|---------|------------|
| RAMO | 2 | = 08 |
| UR | 3 | Catálogo B |
| AÑO | 4 | = 2026 |
| FIN | 1 | Catálogo B |
| FUN | 1 | Catálogo B |
| SF | 2 | Catálogo B |
| RG | 2 | 00, 01, 02, 03 |
| AI | 3 | Catálogo B |
| PP | 4 | Catálogo B + A |
| PARTIDA | 5 | Catálogo A |
| TG | 1 | 1, 2, 3, 7, 8 |
| FF | 1 | Según TG |
| EF | 2 | 00 a 34 |
| PPI | 11 | Longitud |
| AUX2 | 5 | Longitud |
| COP | 2 | Longitud |

## 📚 Catálogos requeridos

1. `Pp_-_Partida_Especifica_2026.xlsx`
2. `Ramo_-_Pp_-_Funcion_-_AI_-_UR_2026.xlsx`
3. `Ramo_Estructura_Economica_2026.xlsx`

## 🛠️ Instalación local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📦 Deploy en Streamlit Cloud

1. Fork este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio
4. Deploy

---
SADER - Secretaría de Agricultura y Desarrollo Rural
