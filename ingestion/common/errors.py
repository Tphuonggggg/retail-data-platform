"""Public error categories never contain connection strings or source values."""


class PipelineError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
