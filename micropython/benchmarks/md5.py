SCALE_FACTOR = 1

MSG_SIZE = 1000
RESULT = 0x33F673B4

MASK32 = 0xFFFFFFFF

h0 = 0
h1 = 0
h2 = 0
h3 = 0

R = (
    7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
    5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
    4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
    6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
)

K = (
    0xD76AA478, 0xE8C7B756, 0x242070DB, 0xC1BDCEEE,
    0xF57C0FAF, 0x4787C62A, 0xA8304613, 0xFD469501,
    0x698098D8, 0x8B44F7AF, 0xFFFF5BB1, 0x895CD7BE,
    0x6B901122, 0xFD987193, 0xA679438E, 0x49B40821,
    0xF61E2562, 0xC040B340, 0x265E5A51, 0xE9B6C7AA,
    0xD62F105D, 0x02441453, 0xD8A1E681, 0xE7D3FBC8,
    0x21E1CDE6, 0xC33707D6, 0xF4D50D87, 0x455A14ED,
    0xA9E3E905, 0xFCEFA3F8, 0x676F02D9, 0x8D2A4C8A,
    0xFFFA3942, 0x8771F681, 0x6D9D6122, 0xFDE5380C,
    0xA4BEEA44, 0x4BDECFA9, 0xF6BB4B60, 0xBEBFBC70,
    0x289B7EC6, 0xEAA127FA, 0xD4EF3085, 0x04881D05,
    0xD9D4D039, 0xE6DB99E5, 0x1FA27CF8, 0xC4AC5665,
    0xF4292244, 0x432AFF97, 0xAB9423A7, 0xFC93A039,
    0x655B59C3, 0x8F0CCC92, 0xFFEFF47D, 0x85845DD1,
    0x6FA87E4F, 0xFE2CE6E0, 0xA3014314, 0x4E0811A1,
    0xF7537E82, 0xBD3AF235, 0x2AD7D2BB, 0xEB86D391,
)


def _left_rotate(x, c):
    return ((x << c) | (x >> (32 - c))) & MASK32


def _md5(initial_msg, initial_len):
    global h0, h1, h2, h3

    length = initial_len

    h0 = 0x67452301
    h1 = 0xEFCDAB89
    h2 = 0x98BADCFE
    h3 = 0x10325476

    new_len = ((length + 8) // 64 + 1) * 64 - 8
    msg = bytearray(new_len + 64)

    for i in range(length):
        msg[i] = initial_msg[i] & 0xFF

    msg[length] = 0x80

    bits_len = (length * 8) & MASK32
    msg[new_len] = bits_len & 0xFF
    msg[new_len + 1] = (bits_len >> 8) & 0xFF
    msg[new_len + 2] = (bits_len >> 16) & 0xFF
    msg[new_len + 3] = (bits_len >> 24) & 0xFF

    for offset in range(0, new_len, 64):
        w = [0] * 16
        for j in range(16):
            base = offset + j * 4
            w[j] = (
                msg[base]
                | (msg[base + 1] << 8)
                | (msg[base + 2] << 16)
                | (msg[base + 3] << 24)
            ) & MASK32

        a = h0
        b = h1
        c = h2
        d = h3

        for k in range(64):
            if k < 16:
                f = ((b & c) | ((~b) & d)) & MASK32
                g = k
            elif k < 32:
                f = ((d & b) | ((~d) & c)) & MASK32
                g = (5 * k + 1) % 16
            elif k < 48:
                f = (b ^ c ^ d) & MASK32
                g = (3 * k + 5) % 16
            else:
                f = (c ^ (b | (~d))) & MASK32
                g = (7 * k) % 16

            temp = d
            d = c
            c = b

            rotate_input = (a + f + K[k] + w[g]) & MASK32
            b = (b + _left_rotate(rotate_input, R[k])) & MASK32
            a = temp

        h0 = (h0 + a) & MASK32
        h1 = (h1 + b) & MASK32
        h2 = (h2 + c) & MASK32
        h3 = (h3 + d) & MASK32


def benchmark():
    length = MSG_SIZE
    for _ in range(SCALE_FACTOR):
        msg = bytearray(length)
        for i in range(length):
            msg[i] = i & 0xFF
        _md5(msg, length)

    digest = (h0 ^ h1 ^ h2 ^ h3) & MASK32
    return digest == RESULT
