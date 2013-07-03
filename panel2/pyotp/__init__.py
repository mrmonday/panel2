from panel2.pyotp.otp import OTP
from panel2.pyotp.hotp import HOTP
from panel2.pyotp.totp import TOTP
import base64
import random


VERSION = '1.3.0'


def random_base32(length=16, random=random.SystemRandom(),
                  chars=base64._b32alphabet.values()):
    return ''.join(
        random.choice(chars)
        for i in xrange(length)
    )
