from enum import Enum
import bitstruct
from AspepCrc import AspepCrc4, AspepCrc16

class EAspepPktType( Enum ):
	Undefine = 0
	Beacon = 5
	Ping = 6
	Error = 15
	Request = 9
	Response = 10
	Async = 9
	pass

class PktDscrpt():
	def __init__( self ):
		# create an empty packet
		self.empty()
		pass

	def __init__( self, bufLen, buf ):
		# create a packet based on input buffer
		self.__init__()
		type = bitstruct.unpack( 'u4', buf, allow_truncated = True )
		
		if bufLen <= 0:
			raise ValueError( "the buffer length is <= 0" )

		match type:
			case EAspepPktType.Beacon:
				self.__decodeBeacon( buf )
				pass

			case EAspepPktType.Ping:
				self.__decodePing( buf )
				pass

			case EAspepPktType.Error:
				self.__decodeErr( buf )
				pass

			case EAspepPktType.Response:
				self.__decodeResp( buf )
				pass

			case _:
				pass
		pass

	def __eq__( self, target ) -> bool:
		if self.type != target.type:
			return False

		# BEACON
		if self.ver == target.ver and self.enCrc == target.enCrc and \
			self.rxsMax == target.rxsMax and self.txsMax == target.txsMax and \
				self.txaMax == target.txaMax:
			return True

		# PING
		if self.c == target.c and self.n == target.n and \
			self.LLID == target.LLID and self.pktNum == target.pktNum and \
				self.crcH == target.crcH:
			return True

		# RESPONSE

		# ASYNC
		
		return False
	
	def empty( self ):
		self.type = EAspepPktType.Undefine
		
		# fields used by BEACON
		self.ver = 0
		self.enCrc = 0
		self.rxsMax = 0
		self.txsMax = 0
		self.txaMax = 0

		# fields used by PING
		self.c = 0
		self.n = 0
		self.LLID = 0
		self.pktNum = 0

		# fields used by ERROR
		self.err = 0
		self.err2 = 0

		# fields used by REQUEST, RESPONSE, ASYNC
		self.payloadLen = 0
		self.payload = bytes()

		# fields for CRC
		self.crc = 0
		self.crcH = 0
		pass
	
	def setBeacon( self, ver, enCrc, rxsMax, txsMax, txaMax ):
		self.type = EAspepPktType.Beacon
		self.ver = ver
		self.enCrc = enCrc
		self.rxsMax = rxsMax
		self.txsMax = txsMax
		self.txaMax = txaMax
		self.crcH = 0
		self.crcH = AspepCrc4().computeCrc( int.from_bytes( self.encode() ) )
		pass

	def setPing( self, c, n, LLID, pktNum ):
		self.type = EAspepPktType.Ping
		self.c = c
		self.n = n
		self.LLID = LLID
		self.pktNum = pktNum
		self.crcH = 0
		self.crcH = AspepCrc4().computeCrc( int.from_bytes( self.encode() ) )
		pass

	def setError( self, err, err2 ):
		self.type = EAspepPktType.Error
		self.err = err
		self.err2 = err2
		self.crcH = 0
		self.crcH = AspepCrc4().computeCrc( int.from_bytes( self.encode() ) )
		pass

	def encodeRequest( self, payloadLen, payload: bytes ):
		self.type = EAspepPktType.Error
		self.payloadLen = payloadLen
		self.crcH = 0
		self.crcH = AspepCrc4().computeCrc( int.from_bytes( self.encode() ) )
		self.payload = payload
		self.crc = AspepCrc16().computeCrc( self.payload )
		pass

	def encodeResponse( self, payloadLen, payload: bytes ):
		self.type = EAspepPktType.Response
		self.payloadLen = payloadLen
		self.crcH = 0
		self.crcH = AspepCrc4().computeCrc( int.from_bytes( self.encode() ) )
		self.payload = payload
		self.crc = AspepCrc16().computeCrc( self.payload )
		pass

	def encode( self ) -> bytes:
		buf = bytes()

		match self.type:
			case EAspepPktType.Beacon:
				# |-4 bit-|-3 bit---|-1 bit--|-6 bit---|-7 bit---|-7 bit---|-4 bit-|
				# |-Type--|-version-|-CRC_EN-|-RXS Max-|-TXS Max-|-TXA Max-|-CRCH--|
				buf = bitstruct.pack( 'u4u3u1u6u7u7u4', \
						 self.type, self.ver, self.enCrc, \
						 self.rxsMax, self.txsMax, self.txaMax, self.crcH )
				pass

			case EAspepPktType.Ping:
				# |-4 bit-|-2 bit-|-2 bit-|-4 bit-|-16 bit-------|-4 bit-|
				# |-Type--|-C-----|-N-----|-LLID--|-Packet Numer-|-CRCH--|
				buf = bitstruct.pack( 'u4u2u2u4u16u4', \
						 self.type, self.c, self.n, \
						 self.LLID, self.pktNum, self.crcH )
				pass

			case EAspepPktType.Error:
				# |-4 bit-|-4 bit-|-8 bit---|-8 bit---|-4 bit-|-4 bit-|
				# |-Type--|-Resrv-|-ErrCode-|-ErrCode-|-Resrv-|-CRCH--|
				resv = 0
				buf = bitstruct.pack( 'u4u4u8u8u4u4', \
						 self.type, resv, self.err, \
						 self.err2, resv, self.crcH )
				pass

			case EAspepPktType.Async:	
				pass

			case EAspepPktType.Request:
				# |-4 bit-|-13 bit-|-11 bit-|-4 bit-| Pkt Pause |-N byte--|-2 byte-|
				# |-Type--|-PL Len-|-Resrv--|-CRCH--|           |-Payload-|-CRC----|
				pass

			case EAspepPktType.Response:
				# |-4 bit-|-13 bit-|-11 bit-|-4 bit-| Pkt Pause |-N byte--|-2 byte-|
				# |-Type--|-PL Len-|-Resrv--|-CRCH--|           |-Payload-|-CRC----|
				pass

		return buf

	def __decodeBeacon( self, buf ):
		self.type, self.ver, self.enCrc, \
			self.rxsMax, self.txsMax, self.txaMax, \
				self.crcH = bitstruct.unpack( 'u4u3u1u6u7u7u4', buf )
		pass

	def __decodePing( self, buf ):
		self.type, self.c, self.n, \
			self.LLID, self.pktNum, \
				self.crcH = bitstruct.unpack( 'u4u2u2u4u16u4', buf )
		pass

	def __decodeErr( self, buf ):
		self.type, _, self.err, self.err2, _, \
			self.crcH = bitstruct.unpack( 'u4u4u8u8u4u4', buf )
		pass

	def __decodeResp( self, buf ):
		self.type, self.payloadLen, _, self.crcH, _, \
			self.crcH = bitstruct.unpack( 'u4u4u8u8u4u4', buf )
		pass
