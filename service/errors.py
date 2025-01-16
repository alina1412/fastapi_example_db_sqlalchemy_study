# from sqlalchemy.exc import IntegrityError


class AnswerNotAddedError(Exception):
    detail: str = "AnswerNotAdded"

    def __init__(self, err):
        self.add_detail = self.detail + f"{err.args}"
