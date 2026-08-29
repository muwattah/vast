"""AI prompts for property analysis. Versioned for reproducibility."""

PROMPT_VERSION = "v1.1"

SYSTEM_PROMPT = """You are an expert Belgian real-estate investment analyst specializing in DIY renovation projects in Antwerp (Flanders).
The investor performs as much renovation work as legally and practically possible themselves.
Return ONLY valid JSON matching the required schema. No markdown, no commentary.
All monetary values in EUR. Use ranges when uncertain. Never invent precise market comps you do not have.
Mark uncertainty clearly in uncertainty_notes and risks.
Do not give legal or tax advice; acquisition costs are indicative only."""

def build_user_prompt(prop_data: dict) -> str:
    return f"""PROPERTY DATA
Title: {prop_data.get('title')}
Price: {prop_data.get('price')}
Living area m²: {prop_data.get('living_area')}
Postal code: {prop_data.get('postal_code')}
District: {prop_data.get('district')}
Type: {prop_data.get('property_type')}
EPC: {prop_data.get('epc_label')} ({prop_data.get('epc_score')})
Bedrooms: {prop_data.get('bedrooms')}
Year built: {prop_data.get('year_built')}
Flags: to_renovate={prop_data.get('is_to_renovate')}, fully={prop_data.get('is_fully_to_renovate')}, investment={prop_data.get('is_investment')}
Description: {(prop_data.get('description') or '')[:800]}

TASK
Analyse as a DIY-focused investor in Antwerp.
Estimate renovation cost range (€/m² bands: light 300-600, medium 600-1000, heavy 1000-1500+).
Estimate indicative after-renovation value range (mark as estimate).
Acquisition costs (registratie + notaris) indicative ~8-12% of price for standard purchase in Flanders – use a range, state uncertainty.
Return JSON with keys:
diy_score, renovation_score, price_score, margin_score, location_score, risk_score, investment_score (1-10),
estimated_renovation_cost_min/max, estimated_after_renovation_value_min/max,
estimated_acquisition_cost_min/max, estimated_total_investment_min/max,
estimated_profit_min/max, roi_min/max,
renovation_level, diy_tasks[], professional_tasks[], opportunities[], risks[], summary, uncertainty_notes[]
"""
