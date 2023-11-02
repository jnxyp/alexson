class Config:
    def __init__(self, allow_comments: bool = True, allows_trailing_comma: bool = True):
        self.allow_comments: bool = allow_comments
        self.allow_trailing_comma: bool = allows_trailing_comma
