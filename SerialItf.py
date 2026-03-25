import serial

class SerialItf:
    def __init__( self ):
        pass

    def open( self ):
        pass

    def close( self ):
        pass

    def write( self, data: bytes ):
        pass

    def read( self, size: int, timeout: float = 0.1 ) -> bytes:
        pass