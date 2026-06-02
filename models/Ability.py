from BaseModel import BaseModel

class Ability(BaseModel):
    table_name = "abilities"

    def __init__(self):
        super().__init__()
