from app.tools.roi_calculator import Inputs, kpis
import csv

def export_kpis_to_csv(inputs: Inputs, path: str):
    data = kpis(inputs)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(data.keys()))
        w.writerow(list(data.values()))
    print(f"Archivo exportado: {path}")

if __name__ == "__main__":
    x = Inputs(spend=150000, revenue=420000, conversions=28, clicks=1900, margin_rate=0.35)
    export_kpis_to_csv(x, "kpis_output.csv")
