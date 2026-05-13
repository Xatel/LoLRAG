from BaseModel import BaseModel

class ChampionStats(BaseModel):
    table_name = "champion_stats"

    def __init__(self):
        super().__init__()

    def insert(self, data: dict) -> int:
        return super().insert(self.table_name, data)

    def get_by_id(self, id: int) -> dict:
        return super().query_by_id(self.table_name, id)

    def update(self, id: int, data: dict) -> bool:
        return super().update(self.table_name, id, data)

    def delete(self, id: int) -> bool:
        return super().delete(self.table_name, id)
