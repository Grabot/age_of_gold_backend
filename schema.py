from pydantic import BaseModel


class SchemaUser(BaseModel):
    first_name: str
    last_name: str
    age: int

    class Config:
        orm_mode = True


class SchemaHexagon(BaseModel):
    q: int
    r: int
    s: int

    class Config:
        orm_mode = True


class SchemaTile(BaseModel):
    type: int

    class Config:
        orm_mode = True
