from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator

OutputFormat = Literal["png", "webp"]

class ProcessingConfig(BaseModel):
    workers: int = Field(default=1, ge=1)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    padding: int = Field(default=0, ge=0)
    output_format: OutputFormat = "png"
    dpi: int = Field(default=72, ge=1)
    overwrite: bool = False
    backend: str = "rembg"

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ProcessingConfig":
        if (self.width is None) != (self.height is None):
            raise ValueError("width and height must be supplied together")
        if self.width is not None and self.padding * 2 >= min(self.width, self.height):
            raise ValueError("padding must leave at least one pixel of inner area")
        return self

class RunConfig(BaseModel):
    input_dir: Path
    output_dir: Path
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
