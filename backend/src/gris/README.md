# GRI Computation Engine

A modular, production-ready computation framework for ESG (Environmental, Social, Governance) standards extraction and analysis based on the Global Reporting Initiative (GRI) framework.

## 📁 Architecture

```
src/
 └── gri_engine/
      ├── __init__.py              # Main module entry point
      ├── example.py               # Usage examples and demonstrations
      ├── README.md                # This file
      └── gri_302/
           ├── __init__.py          # GRI 302 module exports
           ├── computations.py      # All computation logic
           └── README.md            # GRI 302 specific documentation
```

## 🎯 Design Principles

1. **Separation of Concerns**: Schema definitions live in `schemas/`, computation logic in `gri_engine/`
2. **Modular & Extensible**: Each GRI standard gets its own folder with independent computation functions
3. **Type-Safe**: Full type hints using Pydantic v2 for data validation
4. **Defensive Programming**: All functions handle missing data gracefully
5. **Structured Output**: All computations return standardized result dictionaries
6. **Testable**: Functions are pure (no side effects) and independently testable

## 🚀 Quick Start

### Basic Usage: Run All Computations

```python
from src.schemas.output_schemas import AIExtracted_GRI_302, ExtractedData
from src.gri_engine.gri_302 import GRI302Engine

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
print(computations["302_1"]["value"])  # {"total_energy_mj": 1000.0, ...}
print(computations["302_3"]["value"])  # 10.0 (MJ per employee)
```

### Individual Computation Functions

```python
from src.gri_engine.gri_302 import compute_302_1_energy_totals

result = compute_302_1_energy_totals(data)
# Returns: {"computed": True, "value": {...}, "unit": "MJ", "metadata": {...}}
```

## 📊 GRI 302 (Energy) Implementation

The `GRI302Engine` orchestrates computations for five sub-standards:

### 302-1: Energy Consumption Within Organization
**Function**: `compute_302_1_energy_totals(data)`

Returns total, renewable, and non-renewable energy with percentages.

**Output**:
```python
{
    "computed": True,
    "value": {
        "total_energy_mj": 1000.0,
        "renewable_energy_mj": 300.0,
        "non_renewable_energy_mj": 700.0,
        "renewable_percentage": 30.0
    },
    "unit": "MJ",
    "metadata": {
        "base_year": "2024",
        "energy_entries_count": 5,
        "conversion_factors_used": True
    }
}
```

### 302-2: Energy Consumption Outside Organization
**Function**: `compute_302_2_external_energy(data)`

Extracts external energy (purchased electricity, steam, heating, cooling).

**Output**:
```python
{
    "computed": True,
    "value": 5000.0,
    "unit": "MJ",
    "metadata": {
        "base_year": "2024",
        "source": "Purchased electricity, steam, heating, or cooling"
    }
}
```

### 302-3: Energy Intensity
**Function**: `compute_302_3_intensity(data)`

Calculates energy intensity using employee count or revenue as denominator.

**Output**:
```python
{
    "computed": True,
    "value": 10.0,  # MJ per employee
    "unit": "MJ per employee",
    "metadata": {
        "base_year": "2024",
        "denominator_type": "per_employee",
        "denominator_value": 100,
        "total_energy_mj": 1000.0
    }
}
```

### 302-4: Energy Reduction
**Function**: `compute_302_4_reduction(data)`

Calculates absolute and percentage energy reductions from baseline.

**Output**:
```python
{
    "computed": True,
    "value": {
        "reduction_mj": 100.0,
        "reduction_percentage": 9.09,
        "baseline_energy_mj": 1100.0,
        "current_energy_mj": 1000.0
    },
    "unit": "MJ",
    "metadata": {
        "baseline_year": "2020",
        "reporting_year": "2024",
        "years_span": 4
    }
}
```

### 302-5: Product Energy Reduction
**Function**: `compute_302_5_product_reduction(data)`

Extracts product-level energy reduction metrics.

**Output**:
```python
{
    "computed": True,
    "value": 5000.0,
    "unit": "MJ",
    "metadata": {
        "base_year": "2024",
        "category": "Sold products and services"
    }
}
```

## 🔄 Engine Execution Flow

```
AIExtracted_GRI_302 (input data)
           ↓
    GRI302Engine.run()
           ↓
    ┌─────────────────────────────────────────┐
    │ For each sub-standard (302-1 to 302-5): │
    │  1. Check data availability             │
    │  2. Call computation function           │
    │  3. Return structured result            │
    └─────────────────────────────────────────┘
           ↓
    {
        "302_1": {...result...},
        "302_2": {...result...},
        "302_3": {...result...},
        "302_4": {...result...},
        "302_5": {...result...},
        "summary": {
            "computed_count": 3,
            "total_count": 5,
            "availability": {...}
        }
    }
```

## ✅ Result Structure

All computation functions return a standardized dictionary:

```python
{
    "computed": bool,           # Whether computation succeeded
    "value": Any,               # Computed value (dict or float)
    "unit": str,                # Unit of measurement (e.g., "MJ")
    "metadata": dict,           # Additional context
    "reason": Optional[str]     # Error explanation if not computed
}
```

### When `computed=False`:
```python
{
    "computed": False,
    "value": None,
    "unit": "MJ",
    "metadata": {},
    "reason": "Missing required fields: total_energy_mj, employee_count"
}
```

## 🛠️ Validation & Utility Functions

Located in `src/schemas/output_schemas.py`:

### `has_required_fields(data, fields: List[str]) -> bool`
Check if all specified fields are non-None.

### `can_compute(substandard: str, data) -> bool`
Determine if a sub-standard has enough data for computation.

### `extract_subdatasets(data) -> Dict[str, bool]`
Get availability of all sub-standards (deprecated, use engine instead).

### `GRI_302_REQUIREMENTS` (dict)
Mapping of sub-standards to required fields.

```python
GRI_302_REQUIREMENTS = {
    "302_1": ["energy_entries", "total_energy_mj", "renewable_energy_mj", ...],
    "302_2": ["external_energy_mj", "base_year"],
    "302_3": ["total_energy_mj", "employee_count", "intensity_denominator", ...],
    "302_4": ["energy_reduction_mj", "baseline_year", "base_year"],
    "302_5": ["product_energy_reduction_mj", "base_year"]
}
```

## 📚 Data Models

### `AIExtracted_GRI_302` (Main Data Model)
Unified schema consolidating all GRI 302 sub-standards in one flexible model.

**Key Fields**:
- `energy_entries: Optional[List[EnergyEntry]]` - Individual energy records
- `total_energy_mj: Optional[float]` - Total consumption
- `renewable_energy_mj: Optional[float]` - Renewable portion
- `employee_count: Optional[int]` - For intensity calculation
- `revenue: Optional[float]` - Alternative intensity denominator
- `energy_reduction_mj: Optional[float]` - Reduction amount
- `product_energy_reduction_mj: Optional[float]` - Product-level reduction
- `omitted_fields: Dict[str, str]` - Track why fields are missing

### `ExtractedData` (Top-Level Wrapper)
Holds a single detected GRI standard with type-safe union.

```python
class ExtractedData(BaseModel):
    detected_gri: Literal["GRI_302", "GRI_305", "GRI_401"]
    data: Union[AIExtracted_GRI_302, AIExtracted_GRI_305, AIExtracted_GRI_401]
```

## 🔌 Extension Guide: Adding GRI 305 (Emissions)

1. **Create folder structure**:
   ```
   src/gri_engine/gri_305/
    ├── __init__.py
    ├── computations.py
    └── README.md
   ```

2. **Define schema** in `schemas/output_schemas.py`:
   ```python
   class AIExtracted_GRI_305(BaseModel):
       # Define fields for emissions...
   ```

3. **Implement computations** in `gri_305/computations.py`:
   ```python
   def compute_305_1_direct_emissions(data: AIExtracted_GRI_305) -> Dict[str, Any]:
       # Implementation...
   
   GRI_305_FUNCTIONS = {
       "305_1": compute_305_1_direct_emissions,
       # ... more functions
   }
   
   class GRI305Engine:
       def run(self, data: AIExtracted_GRI_305) -> Dict[str, Any]:
           # Implementation...
   ```

4. **Export from main module** in `gri_engine/__init__.py`:
   ```python
   from src.gri_engine.gri_305 import GRI305Engine
   ```

## 📝 Examples

See `src/gri_engine/example.py` for complete working examples:

1. **Complete Computation** - All sub-standards with full data
2. **Partial Data** - Some sub-standards available
3. **Missing Data** - Graceful error handling
4. **Direct Functions** - Advanced usage with individual functions

Run examples:
```bash
python src/gri_engine/example.py
```

## 🧪 Testing

All computation functions are pure and independently testable:

```python
def test_compute_302_1():
    data = AIExtracted_GRI_302(
        energy_entries=[],
        total_energy_mj=1000.0,
        renewable_energy_mj=300.0,
        non_renewable_energy_mj=700.0,
        base_year="2024"
    )
    result = compute_302_1_energy_totals(data)
    
    assert result["computed"] == True
    assert result["value"]["total_energy_mj"] == 1000.0
    assert result["value"]["renewable_percentage"] == 30.0
```

## 🚀 Performance Considerations

- **All computations O(1) or O(n)** where n = number of energy entries
- **Lazy evaluation**: Only computable sub-standards are executed
- **Memory efficient**: No intermediate data structures; streaming computation possible

## 📖 API Reference

### GRI302Engine

**Methods**:
- `run(data: AIExtracted_GRI_302) -> Dict[str, Any]`

**Attributes**:
- `functions: Dict[str, Callable]` - Function registry

### Computation Functions

All follow the signature:
```python
def compute_302_X_*(data: AIExtracted_GRI_302) -> Dict[str, Any]
```

## 🔐 Backward Compatibility

Legacy functions in `output_schemas.py` are maintained with deprecation warnings:
- `compute_energy_intensity()` → Use `compute_302_3_intensity()` instead
- `compute_renewable_percentage()` → Use engine results
- `compute_energy_reduction_percentage()` → Use `compute_302_4_reduction()` instead
- `extract_subdatasets()` → Use `engine.run()` instead

## 📄 License & Usage

This module is part of the Hackathon ESG Extraction System.

For questions or issues, refer to the project documentation.
