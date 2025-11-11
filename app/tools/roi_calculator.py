from dataclasses import dataclass
from typing import Optional

@dataclass
class Inputs:
    spend: float
    revenue: Optional[float] = None
    clicks: Optional[int] = None
    leads: Optional[int] = None
    conversions: Optional[int] = None
    margin_rate: Optional[float] = None  # 0.35 = 35%

def _r(v, n=2):
    return None if v is None else round(v, n)

def kpis(x: Inputs) -> dict:
    conv = x.conversions if x.conversions is not None else x.leads
    cpa  = (x.spend / conv)      if (conv and conv > 0) else None
    cpc  = (x.spend / x.clicks)  if (x.clicks and x.clicks > 0) else None
    roas = (x.revenue / x.spend) if (x.revenue is not None and x.spend) else None
    cvr  = (conv / x.clicks)     if (conv and x.clicks) else None
    mer  = roas
    gm   = (x.revenue * x.margin_rate) if (x.revenue is not None and x.margin_rate is not None) else None
    profit = (gm - x.spend) if (gm is not None) else None
    be_roas = (1 / x.margin_rate) if (x.margin_rate and x.margin_rate > 0) else None
    be_cpa = ((x.revenue / be_roas) / conv) if (x.revenue and be_roas and conv) else None
    return {
        "CPA": _r(cpa), "CPC": _r(cpc), "CVR": _r(cvr, 4),
        "ROAS": _r(roas, 2), "MER": _r(mer, 2),
        "GrossMargin": _r(gm), "Profit": _r(profit),
        "BE_ROAS": _r(be_roas, 2), "BE_CPA": _r(be_cpa)
    }
