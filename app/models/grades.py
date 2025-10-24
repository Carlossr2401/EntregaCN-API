from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from typing import Optional
from datetime import datetime
import uuid

# --- Modelo para Creación (POST) ---
# El cliente solo debe enviar estos datos.
# ID y Timestamps se generan automáticamente.

class GradeCreateModel(BaseModel):
    Clase: str = Field(..., min_length=1, max_length=100)
    Alumno: str = Field(..., min_length=1, max_length=100)
    Nota: int = Field(..., ge=0, le=10) # Nota debe estar entre 0 y 10
    Fecha: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('Fecha')
    def validate_iso_date(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError("La fecha debe estar en formato ISO")

    class Config:
        json_schema_extra = {
            "example": {
                "Clase": "Programación",
                "Alumno": "Carlos Gómez",
                "Nota": 7
            }
        }


# --- Modelo para Actualización (PUT) ---
# Sigue igual, todos los campos opcionales.

class UpdateGradeModel(BaseModel):
    # Permite a Pydantic leer desde atributos de objeto (ORM)
    model_config = ConfigDict(from_attributes=True) 
    
    Clase: Optional[str] = Field(None, min_length=1, max_length=100)
    Alumno: Optional[str] = Field(None, min_length=1, max_length=100)
    Nota: Optional[int] = Field(None, ge=0, le=10)
    Fecha: Optional[str] = None

    @field_validator('Fecha')
    def validate_iso_date_optional(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError("La fecha debe estar en formato ISO")


# --- Modelo Principal / de Respuesta (GET) ---
# Este modelo representa el objeto COMPLETO, tal como está en la BBDD.

class GradeModel(BaseModel):
    # Permite a Pydantic leer desde atributos de objeto (ORM)
    model_config = ConfigDict(from_attributes=True) 

    # Campos gestionados por la BBDD
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Campos del usuario
    Clase: str
    Alumno: str
    Nota: int
    Fecha: datetime # La BBDD devolverá un objeto datetime