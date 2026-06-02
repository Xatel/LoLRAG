from BaseModel import BaseModel

class AbilityLevel(BaseModel):
    table_name = "ability_levels"

    def __init__(self):
        super().__init__()
