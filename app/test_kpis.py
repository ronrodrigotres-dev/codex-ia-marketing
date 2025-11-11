from app.tools.roi_calculator import Inputs, kpis

if __name__ == "__main__":
    x = Inputs(spend=150000, revenue=420000, conversions=28, clicks=1900, margin_rate=0.35)
    out = kpis(x)
    print(out)
    assert out["ROAS"] == 2.8
