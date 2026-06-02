from BaseModel import BaseModel

class Champion(BaseModel):
    table_name = "champions"

    def __init__(self):
        super().__init__()
