import argparse, pandas as pd, math, sys
from pathlib import Path
from typing import Optional, Dict
from app.tools.roi_calculator import Inputs, kpis

ALIASES = {
    "spend": {"spend","cost","costo","inversion","gasto","importe_gastado","amount_spent"},
    "revenue": {"revenue","ingresos","valor_ventas","conversion_value","purchase_value","ventas","gmv"},
    "clicks": {"clicks","clics"},
    "leads": {"leads","registros","formularios","contactos"},
    "conversions": {"conversions","conv","purchases","compras","orders","ventas_cnt"},
    "margin_rate": {"margin_rate","margen","margen_%","profit_margin","gross_margin_rate"}
}

def norm(s:str)->str:
    return s.strip().lower().replace(" ", "_")

def find_col(cols)->Dict[str, Optional[str]]:
    cols_n = {norm(c): c for c in cols}
    out = {k: None for k in ALIASES}
    for target, names in ALIASES.items():
        for n in names:
            if n in cols_n:
                out[target] = cols_n[n]; break
    if out["spend"] is None:  # clave
        raise ValueError("Columna de gasto no encontrada. Aliases: " + ", ".join(sorted(ALIASES["spend"])))
    return out

def to_float(v):
    if v is None: return None
    if isinstance(v, (int,float)):
        if isinstance(v, float) and math.isnan(v): return None
        return float(v)
    s = str(v).strip()
    if s == "" or s.lower() in {"na","none","null"}: return None
    s = s.replace("\u00A0","").replace(" ","")
    if s.count(",")>0 and s.count(".")>0:
        if s.rfind(",")>s.rfind("."):
            s = s.replace(".","").replace(",",".")
        else:
            s = s.replace(",","")
    else:
        s = s.replace(",",".")
    try: return float(s)
    except: return None

def to_int_safe(v):
    f = to_float(v)
    return int(f) if f is not None else None

def compute_row(r, m):
    x = Inputs(
        spend = float(to_float(r[m["spend"]])),
        revenue = to_float(r[m["revenue"]]) if m["revenue"] else None,
        clicks = to_int_safe(r[m["clicks"]]) if m["clicks"] else None,
        leads = to_int_safe(r[m["leads"]]) if m["leads"] else None,
        conversions = to_int_safe(r[m["conversions"]]) if m["conversions"] else None,
        margin_rate = to_float(r[m["margin_rate"]]) if m["margin_rate"] else None
    )
    return kpis(x)

def main():
    ap = argparse.ArgumentParser(description="Calcula KPIs de performance por fila")
    ap.add_argument("--input","--in", dest="inp", required=True, help="CSV de entrada")
    ap.add_argument("--output","--out", dest="out", required=True, help="CSV de salida")
    ap.add_argument("--sep", default=",", help="Separador CSV (por defecto ,)")
    args = ap.parse_args()

    inp = Path(args.inp);  out = Path(args.out)
    if not inp.exists():
        print(f"ERROR: no existe {inp}", file=sys.stderr); sys.exit(2)

    df = pd.read_csv(inp, sep=args.sep, dtype=str, encoding="utf-8", engine="python")
    mapping = find_col(df.columns)
    res = df.apply(lambda r: compute_row(r, mapping), axis=1, result_type="expand")
    cols = ["CPA","CPC","CVR","ROAS","MER","GrossMargin","Profit","BE_ROAS","BE_CPA"]
    res = res[cols]
    df_out = pd.concat([df, res], axis=1)
    df_out.to_csv(out, index=False, encoding="utf-8")
    print(f"OK: {len(df_out)} filas → {out}")

if __name__ == "__main__":
    main()
