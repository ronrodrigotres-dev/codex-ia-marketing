#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de línea de comandos para calcular KPIs de marketing (CPA, ROAS, etc.)
a partir de un archivo CSV de entrada.

Este script mapea automáticamente las columnas del CSV (ej. "costo", "inversion")
a nombres estándar (ej. "spend") y calcula los KPIs fila por fila.

Incluye un lector de CSV robusto que intenta autodetectar separadores
y manejar archivos con formato "sucio" (comillas mal puestas).
"""

# --- Importaciones de la Librería Estándar ---
import argparse
import math
import sys
import csv
from io import StringIO
from pathlib import Path
from typing import Optional, Dict

# --- Importaciones de Terceros (Pandas) ---
import pandas as pd

# --- Importaciones Locales de la Aplicación ---
try:
    from app.tools.roi_calculator import Inputs, kpis
except ImportError:
    # Fallback por si la estructura de 'app' no está disponible
    # Esto asume que 'tools' está en la misma carpeta
    from tools.roi_calculator import Inputs, kpis

# --- Constantes ---

# Mapeo de aliases de columnas (normalizados) a nombres de métricas estándar
ALIASES = {
    "spend": {"spend", "cost", "costo", "inversion", "gasto", "importe_gastado", "amount_spent"},
    "revenue": {"revenue", "ingresos", "valor_ventas", "conversion_value", "purchase_value", "ventas", "gmv"},
    "clicks": {"clicks", "clics"},
    "leads": {"leads", "registros", "formularios", "contactos"},
    "conversions": {"conversions", "conv", "purchases", "compras", "orders", "ventas_cnt"},
    "margin_rate": {"margin_rate", "margen", "margen_%", "profit_margin", "gross_margin_rate"}
}

# --- Funciones de Normalización y Mapeo ---

def norm(s: str) -> str:
    """Normaliza un nombre de columna: minúsculas, sin espacios y guion bajo."""
    return s.strip().lower().replace(" ", "_")

def find_col(cols: list[str]) -> Dict[str, Optional[str]]:
    """
    Encuentra la primera coincidencia de alias en las columnas del DataFrame.
    'cols' es la lista de nombres de columnas del CSV.
    Devuelve un diccionario mapeando métrica estándar a nombre de columna original.
    """
    cols_n = {norm(c): c for c in cols}
    out = {k: None for k in ALIASES}
    
    for target_metric, alias_names in ALIASES.items():
        for n in alias_names:
            if n in cols_n:
                out[target_metric] = cols_n[n]
                break # Encontrada la primera coincidencia para esta métrica
    
    if out["spend"] is None:  # El gasto (spend) es una columna clave y obligatoria
        raise ValueError("Columna de gasto no encontrada. Aliases buscados: " + ", ".join(sorted(ALIASES["spend"])))
    
    return out

# --- Funciones de Conversión de Tipos (Robustas) ---

def to_float(v) -> Optional[float]:
    """
    Convierte de forma robusta un valor a float, manejando Nones,
    formatos numéricos (ej. "1.000,50" o "1,000.50") y strings vacíos.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and math.isnan(v):
            return None
        return float(v)
    
    s = str(v).strip()
    if s == "" or s.lower() in {"na", "none", "null"}:
        return None
    
    # Limpiar espacios (incluido non-breaking space \u00A0)
    s = s.replace("\u00A0", "").replace(" ", "")
    
    # Detección de formato (europeo vs americano)
    count_comma = s.count(",")
    count_dot = s.count(".")
    
    if count_comma > 0 and count_dot > 0:
        # Asumir que el último es el decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")  # Formato 1.000,50 -> 1000.50
        else:
            s = s.replace(",", "")  # Formato 1,000.50 -> 1000.50
    else:
        # Si solo hay comas, asumir que es decimal
        s = s.replace(",", ".")
        
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def to_int_safe(v) -> Optional[int]:
    """Convierte a float de forma segura y luego a int, manejando Nones."""
    f = to_float(v)
    return int(f) if f is not None else None

# --- Función de Lectura de CSV (Robusta) ---

def read_csv_robusto(path: Path, sep_hint: Optional[str] = None) -> pd.DataFrame:
    """
    Intenta leer un CSV usando 3 métodos, desde el más simple hasta el más robusto,
    para manejar diferentes separadores, comillas y líneas defectuosas.
    """
    # 1) Intento directo con el separador indicado (o coma por defecto)
    try:
        return pd.read_csv(path, sep=(sep_hint or ","), dtype=str, encoding="utf-8", engine="python")
    except Exception:
        pass  # Falla silenciosamente y pasa al siguiente método
    
    # 2) Autodetección de separador/quote con 'csv.Sniffer'
    # Leemos solo una parte del archivo para detectar el dialecto
    txt = path.read_text(encoding="utf-8", errors="ignore")
    try:
        dialect = csv.Sniffer().sniff(txt[:10000], delimiters=[",", ";", "|", "\t"])
        return pd.read_csv(
            StringIO(txt),
            sep=dialect.delimiter,
            dtype=str,
            quotechar=dialect.quotechar,
            doublequote=True, # Estándar CSV
            escapechar="\\", # Asumir escape de barra
            engine="python"
        )
    except Exception:
        pass # Falla silenciosamente y pasa al último método
    
    # 3) Modo "desesperado": sin comillas, saltando líneas malas (causa del ParserError)
    try:
        return pd.read_csv(
            StringIO(txt),
            sep=(sep_hint or ";"), # Asumir ; si la coma falló
            dtype=str,
            engine="python",
            quotechar=None, # No procesar comillas
            quoting=csv.QUOTE_NONE, # No procesar comillas
            on_bad_lines="skip", # Saltar filas que pandas no pueda analizar
            escapechar="\\"
        )
    except Exception as e:
        # Si todo falla, lanzar un error claro
        raise RuntimeError(f"CSV malformado. No se pudo leer {path}. Revisa separador y comillas. Detalle: {e}")

# --- Lógica Principal ---

def compute_row(r: pd.Series, m: Dict[str, str]) -> pd.Series:
    """Calcula todos los KPIs para una sola fila (Series) del DataFrame."""
    
    # *** MEJORA ***
    # El 'spend' (gasto) es obligatorio. Si es None (ej. celda vacía),
    # tu `float(to_float(r[...]))` original fallaría con un TypeError.
    # Lo asignamos a 0.0 para evitar el error.
    spend_val = to_float(r[m["spend"]])
    
    x = Inputs(
        spend=0.0 if spend_val is None else spend_val,
        revenue=to_float(r[m["revenue"]]) if m["revenue"] else None,
        clicks=to_int_safe(r[m["clicks"]]) if m["clicks"] else None,
        leads=to_int_safe(r[m["leads"]]) if m["leads"] else None,
        conversions=to_int_safe(r[m["conversions"]]) if m["conversions"] else None,
        margin_rate=to_float(r[m["margin_rate"]]) if m["margin_rate"] else None
    )
    
    # Asumimos que kpis(x) devuelve un diccionario o un objeto
    # que se puede convertir en una Serie de pandas.
    return kpis(x)

def main():
    """Función principal del script: parsear argumentos y procesar el CSV."""
    
    ap = argparse.ArgumentParser(description="Calcula KPIs de performance por fila")
    ap.add_argument("--input", "--in", dest="inp", required=True, help="CSV de entrada")
    ap.add_argument("--output", "--out", dest="out", required=True, help="CSV de salida")
    ap.add_argument("--sep", default=None, help="Separador CSV (sugerencia, ej. ';'). Si no se da, se autodetecta.")
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    
    if not inp.exists():
        print(f"ERROR: No existe el archivo de entrada {inp}", file=sys.stderr)
        sys.exit(2)

    try:
        # *** INTEGRACIÓN ***
        # Reemplazamos la lectura simple por la función robusta
        df = read_csv_robusto(inp, sep_hint=args.sep)
        
        mapping = find_col(df.columns)
        
        # Aplicar el cálculo de KPIs fila por fila
        res = df.apply(lambda r: compute_row(r, mapping), axis=1, result_type="expand")
        
        # Definir las columnas de KPIs que queremos en el resultado
        cols = ["CPA", "CPC", "CVR", "ROAS", "MER", "GrossMargin", "Profit", "BE_ROAS", "BE_CPA"]
        
        # Asegurarse de que solo se usen las columnas que existen en 'res'
        # (por si kpis() no devolvió alguna)
        res_cols = [c for c in cols if c in res.columns]
        res = res[res_cols]
        
        # Unir el DataFrame original con los resultados
        df_out = pd.concat([df, res], axis=1)
        
        # Guardar el archivo de salida
        df_out.to_csv(out, index=False, encoding="utf-8", sep=";") # Usar ; para salida
        
        print(f"OK: {len(df_out)} filas procesadas → {out}")
        
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR Inesperado: {e}", file=sys.stderr)
        sys.exit(1)

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()