from BaseModel import BaseModel

class ContentChunk(BaseModel):
    table_name = "content_chunks"

    def __init__(self):
        super().__init__()
