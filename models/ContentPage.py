from BaseModel import BaseModel

class ContentPage(BaseModel):
    table_name = "content_pages"

    def __init__(self):
        super().__init__()
