from qrtools import QR
import os
class QRCodeGenerator(object):
   def __init__(self):
      self.dst = ""

   def generate_qrcode(self, data, filename):
       my_QR = QR(data = data)
       my_QR.encode()

       # command to move the QR code to the desktop
       os.system("sudo mv " + my_QR.filename + " " + filename)
