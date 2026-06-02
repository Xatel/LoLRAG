from BaseModel import BaseModel

class SearchHistory(BaseModel):
    table_name = "search_history"

    def __init__(self):
        super().__init__()
