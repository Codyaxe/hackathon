from typing import Literal, Optional

from pydantic import BaseModel, Field











class Omission401(BaseModel):
    field_name: Literal[
                        "UNIMPLEMENTED"
                    ] = Field(
                        description=(
                            "The exact field name that could not be populated. "
                            "Must be one of the defined GRI 302 fields. "
                            "Do not invent field names outside this list."
                        )
                    )

    reason: str = Field(
        description=(
            "Specific reason why this field is absent. "
            "Reference the source material directly — e.g. 'organization stated they have no baseline year', "
            "'document only covers electricity, no fuel records provided'. "
            "Do not use generic reasons like 'not found' or 'missing'."
        )
    )