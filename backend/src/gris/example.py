"""
GRI 302 Computation Engine - Usage Examples

This file demonstrates how to use the refactored GRI extraction and computation system.
"""

from src.schemas.output_schemas import (
    AIExtracted_GRI_302,
    ExtractedData,
    ConversionFactors,
)
from schemas.MetricsSchemas.GRI_302_Metrics import EnergyEntry
from src.dependencies.engines import GRI302Engine
import json


# ============================================================================
# EXAMPLE 1: Complete GRI 302 Computation with All Sub-Standards
# ============================================================================

def example_complete_gri302_computation():
    """
    Example: Compute all GRI 302 sub-standards with complete data.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Complete GRI 302 Computation")
    print("=" * 80)
    
    # Create energy entries
    energy_entries = [
        EnergyEntry(
            energy_type="electricity",
            value=5000.0,
            unit="kWh",
            converted_mj=18000.0,
            is_renewable=True,
            source="Grid renewable"
        ),
        EnergyEntry(
            energy_type="natural_gas",
            value=2000.0,
            unit="m3",
            converted_mj=80000.0,
            is_renewable=False,
            source="Building heating"
        ),
    ]
    
    # Create extracted data
    data = AIExtracted_GRI_302(
        # GRI 302-1: Energy Consumption
        energy_entries=energy_entries,
        total_energy_mj=98000.0,
        renewable_energy_mj=18000.0,
        non_renewable_energy_mj=80000.0,
        
        # GRI 302-2: External Energy
        external_energy_mj=5000.0,
        
        # GRI 302-3: Intensity
        employee_count=500,
        revenue=50000000.0,
        intensity_denominator="per_employee",
        
        # GRI 302-4: Energy Reduction
        energy_reduction_mj=12000.0,
        baseline_year="2020",
        
        # GRI 302-5: Product Reduction
        product_energy_reduction_mj=5000.0,
        
        # Metadata
        conversion_factors=ConversionFactors(
            electricity_kwh_to_mj=3.6,
            diesel_liter_to_mj=36.54
        ),
        base_year="2024",
    )
    
    # Wrap in top-level result
    result = ExtractedData(detected_gri="GRI_302", data=data)
    
    # Run engine
    engine = GRI302Engine()
    computations = engine.run(result.data)
    
    # Display results
    print(f"\n✓ GRI Standard: {result.detected_gri}")
    print(f"✓ Base Year: {computations['summary']['base_year']}")
    print(f"✓ Computed Results: {computations['summary']['computed_count']}/{computations['summary']['total_count']}")
    
    print("\n--- 302-1: Energy Consumption ---")
    if computations["302_1"]["computed"]:
        v = computations["302_1"]["value"]
        print(f"  Total Energy: {v['total_energy_mj']:.2f} {computations['302_1']['unit']}")
        print(f"  Renewable: {v['renewable_energy_mj']:.2f} MJ ({v['renewable_percentage']:.1f}%)")
        print(f"  Non-Renewable: {v['non_renewable_energy_mj']:.2f} MJ")
        print(f"  Energy Entries: {computations['302_1']['metadata']['energy_entries_count']}")
    else:
        print(f"  ✗ Not computed: {computations['302_1']['reason']}")
    
    print("\n--- 302-2: External Energy ---")
    if computations["302_2"]["computed"]:
        print(f"  External Energy: {computations['302_2']['value']:.2f} {computations['302_2']['unit']}")
        print(f"  Source: {computations['302_2']['metadata']['source']}")
    else:
        print(f"  ✗ Not computed: {computations['302_2']['reason']}")
    
    print("\n--- 302-3: Energy Intensity ---")
    if computations["302_3"]["computed"]:
        m = computations["302_3"]["metadata"]
        print(f"  Intensity: {computations['302_3']['value']:.2f} {computations['302_3']['unit']}")
        print(f"  Denominator: {m['denominator_type']} ({m['denominator_value']:.0f})")
        print(f"  Total Energy: {m['total_energy_mj']:.2f} MJ")
    else:
        print(f"  ✗ Not computed: {computations['302_3']['reason']}")
    
    print("\n--- 302-4: Energy Reduction ---")
    if computations["302_4"]["computed"]:
        v = computations["302_4"]["value"]
        m = computations["302_4"]["metadata"]
        print(f"  Reduction: {v['reduction_mj']:.2f} MJ ({v['reduction_percentage']:.1f}%)")
        print(f"  Baseline: {m['baseline_year']} | Reporting: {m['reporting_year']}")
        print(f"  Baseline Energy: {v['baseline_energy_mj']:.2f} MJ")
        print(f"  Current Energy: {v['current_energy_mj']:.2f} MJ")
        if m['years_span']:
            print(f"  Time Period: {m['years_span']} years")
    else:
        print(f"  ✗ Not computed: {computations['302_4']['reason']}")
    
    print("\n--- 302-5: Product Energy Reduction ---")
    if computations["302_5"]["computed"]:
        print(f"  Product Reduction: {computations['302_5']['value']:.2f} {computations['302_5']['unit']}")
        print(f"  Category: {computations['302_5']['metadata']['category']}")
    else:
        print(f"  ✗ Not computed: {computations['302_5']['reason']}")


# ============================================================================
# EXAMPLE 2: Partial Data (302-1 and 302-3 Only)
# ============================================================================

def example_partial_data():
    """
    Example: Compute with partial data (only some sub-standards available).
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Partial Data Computation (302-1 and 302-3 Only)")
    print("=" * 80)
    
    # Only provide data for 302-1 and 302-3
    data = AIExtracted_GRI_302(
        # GRI 302-1: Energy Consumption
        energy_entries=[],
        total_energy_mj=50000.0,
        renewable_energy_mj=10000.0,
        non_renewable_energy_mj=40000.0,
        
        # GRI 302-3: Intensity
        employee_count=200,
        
        # Metadata
        base_year="2024",
        omitted_fields={
            "external_energy_mj": "Not reported by organization",
            "energy_reduction_mj": "Baseline data not available",
            "product_energy_reduction_mj": "No product data tracked"
        }
    )
    
    # Run engine
    engine = GRI302Engine()
    computations = engine.run(data)
    
    # Display summary
    print(f"\n✓ Computed Results: {computations['summary']['computed_count']}/{computations['summary']['total_count']}")
    print(f"✓ Sub-standards Available:")
    for substandard, available in computations['summary']['availability'].items():
        status = "✓" if available else "✗"
        print(f"  {status} {substandard}")
    
    print(f"\n✓ Omitted Fields ({len(data.omitted_fields)}):")
    for field, reason in data.omitted_fields.items():
        print(f"  - {field}: {reason}")
    
    # Show computed results
    print("\n--- Computed Sub-standards ---")
    if computations["302_1"]["computed"]:
        print(f"✓ 302-1: Total energy {computations['302_1']['value']['total_energy_mj']:.0f} MJ")
    
    if computations["302_3"]["computed"]:
        print(f"✓ 302-3: Intensity {computations['302_3']['value']:.1f} {computations['302_3']['unit']}")


# ============================================================================
# EXAMPLE 3: Missing Required Data
# ============================================================================

def example_missing_data():
    """
    Example: Demonstrate graceful handling of missing data.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Missing Required Data")
    print("=" * 80)
    
    # Only provide base_year, missing all actual data
    data = AIExtracted_GRI_302(
        base_year="2024",
        omitted_fields={
            "total_energy_mj": "Data not extracted from document",
            "renewable_energy_mj": "Renewable breakdown not provided",
            "employee_count": "Employee count not found in source material"
        }
    )
    
    # Run engine
    engine = GRI302Engine()
    computations = engine.run(data)
    
    # Display results
    print(f"\n✓ Computed Results: {computations['summary']['computed_count']}/{computations['summary']['total_count']}")
    
    print(f"\nOmitted Fields ({len(data.omitted_fields)}):")
    for field, reason in data.omitted_fields.items():
        print(f"  - {field}: {reason}")
    
    print("\n--- Failed Computations (with Reasons) ---")
    for substandard in ["302_1", "302_2", "302_3", "302_4", "302_5"]:
        result = computations[substandard]
        if not result["computed"]:
            print(f"✗ {substandard}: {result['reason']}")


# ============================================================================
# EXAMPLE 4: Accessing Individual Computation Functions
# ============================================================================

def example_individual_functions():
    """
    Example: Use individual computation functions directly (advanced usage).
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Direct Function Calls (Advanced)")
    print("=" * 80)
    
    from src.gris.gri_302_computations import (
        compute_302_1_energy_totals,
        compute_302_3_intensity,
    )
    
    data = AIExtracted_GRI_302(
        # GRI 302-1: Energy Consumption (required for 302-1 computation)
        energy_entries=[],
        total_energy_mj=1000.0,
        renewable_energy_mj=250.0,
        non_renewable_energy_mj=750.0,
        
        # GRI 302-3: Intensity (required for 302-3 computation)
        employee_count=50,
        
        # Metadata
        base_year="2024"
    )
    
    # Call individual functions
    result_302_1 = compute_302_1_energy_totals(data)
    result_302_3 = compute_302_3_intensity(data)
    
    print("\n✓ Direct Function Call Results:")
    
    # Display 302-1 result with error handling
    if result_302_1['computed']:
        print(f"  ✓ 302-1 (Energy Totals):")
        print(f"      Total Energy: {result_302_1['value']['total_energy_mj']:.1f} MJ")
        print(f"      Renewable: {result_302_1['value']['renewable_percentage']:.1f}%")
    else:
        print(f"  ✗ 302-1: {result_302_1['reason']}")
    
    # Display 302-3 result with error handling
    if result_302_3['computed']:
        print(f"  ✓ 302-3 (Intensity):")
        print(f"      Value: {result_302_3['value']:.1f} {result_302_3['unit']}")
    else:
        print(f"  ✗ 302-3: {result_302_3['reason']}")


# ============================================================================
# EXAMPLE 5: Raw Engine Output (Complete Dataset)
# ============================================================================

def example_complete_gri302_raw_output():
    """
    Example: Print raw JSON output from GRI302Engine with complete data.
    
    This demonstrates the full structure of the computation engine's return value.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Raw Engine Output (Complete Dataset)")
    print("=" * 80)
    
    # Create energy entries
    energy_entries = [
        EnergyEntry(
            energy_type="electricity",
            value=5000.0,
            unit="kWh",
            converted_mj=18000.0,
            is_renewable=True,
            source="Grid renewable"
        ),
        EnergyEntry(
            energy_type="natural_gas",
            value=2000.0,
            unit="m3",
            converted_mj=80000.0,
            is_renewable=False,
            source="Building heating"
        ),
    ]
    
    # Create extracted data
    data = AIExtracted_GRI_302(
        # GRI 302-1: Energy Consumption
        energy_entries=energy_entries,
        total_energy_mj=98000.0,
        renewable_energy_mj=18000.0,
        non_renewable_energy_mj=80000.0,
        
        # GRI 302-2: External Energy
        external_energy_mj=5000.0,
        
        # GRI 302-3: Intensity
        employee_count=500,
        revenue=50000000.0,
        intensity_denominator="per_employee",
        
        # GRI 302-4: Energy Reduction
        energy_reduction_mj=12000.0,
        baseline_year="2020",
        
        # GRI 302-5: Product Reduction
        product_energy_reduction_mj=5000.0,
        
        # Metadata
        conversion_factors=ConversionFactors(
            electricity_kwh_to_mj=3.6,
            diesel_liter_to_mj=36.54
        ),
        base_year="2024",
    )
    
    # Wrap in top-level result
    result = ExtractedData(detected_gri="GRI_302", data=data)
    
    # Run engine
    engine = GRI302Engine()
    computations = engine.run(result.data)
    
    # Print raw JSON output
    print("\n=== RAW ENGINE OUTPUT ===\n")
    print(json.dumps(computations, indent=2))


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█" * 80)
    print("GRI 302 COMPUTATION ENGINE - USAGE EXAMPLES")
    print("█" * 80)
    
    # Run all examples
    example_complete_gri302_computation()
    example_partial_data()
    example_missing_data()
    example_individual_functions()
    example_complete_gri302_raw_output()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80 + "\n")
