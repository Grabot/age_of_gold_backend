from pydantic import BaseModel


class SchemaUser(BaseModel):
    first_name: str
    last_name: str
    age: int

    class Config:
        orm_mode = True
