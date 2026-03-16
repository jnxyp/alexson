class Config:
    def __init__(
        self,
        allow_comments: bool = True,
        allows_trailing_comma: bool = True,
        allow_duplicate_keys: bool = False,
    ):
        self.allow_comments: bool = allow_comments
        self.allow_trailing_comma: bool = allows_trailing_comma
        self.allow_duplicate_keys: bool = allow_duplicate_keys
