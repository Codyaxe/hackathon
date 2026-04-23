"""
GRI Computation Engine

Modular computation framework for ESG (Environmental, Social, Governance) standards
based on the Global Reporting Initiative (GRI) framework.

Currently Supported:
    - GRI 302: Energy
    - GRI 305: Emissions (Placeholder)
    - GRI 401: Employment (Placeholder)

Example:
    from src.schemas.output_schemas import AIExtracted_GRI_302, ExtractedData
    from src.dependencies.engines import GRI302Engine
    
    # Create extracted data
    data = AIExtracted_GRI_302(
        total_energy_mj=1000.0,
        renewable_energy_mj=300.0,
        non_renewable_energy_mj=700.0,
        employee_count=100,
        base_year="2024"
    )
    
    # Wrap in top-level result
    result = ExtractedData(detected_gri="GRI_302", data=data)
    
    # Run computation engine
    engine = GRI302Engine()
    computations = engine.run(result.data)
    
    # Access results
    print(f"Total energy: {computations['302_1']['value']['total_energy_mj']} MJ")
    print(f"Intensity: {computations['302_3']['value']} {computations['302_3']['unit']}")
"""

# Expose GRI 302 module (orchestration: ``from src.dependencies.engines import GRI302Engine``)
from src.gris.gri_302_computations import (
    compute_302_1_energy_totals,
    compute_302_2_external_energy,
    compute_302_3_intensity,
    compute_302_4_reduction,
    compute_302_5_product_reduction,
    GRI_302_FUNCTIONS,
)

__all__ = [
    "compute_302_1_energy_totals",
    "compute_302_2_external_energy",
    "compute_302_3_intensity",
    "compute_302_4_reduction",
    "compute_302_5_product_reduction",
    "GRI_302_FUNCTIONS",
]
