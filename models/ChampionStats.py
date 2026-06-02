from BaseModel import BaseModel

class ChampionStats(BaseModel):
    table_name = "champion_stats"

    def __init__(self):
        super().__init__()
