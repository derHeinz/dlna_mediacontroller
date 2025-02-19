class RequestInvalidException(Exception):
    pass

class RequestCannotBeHandeledException(Exception):
    
     def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)
