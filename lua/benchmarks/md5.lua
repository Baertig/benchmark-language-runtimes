local SCALE_FACTOR = 1
local MSG_SIZE = 1000
local RESULT = 0x33f673b4 

local h0 = 0
local h1 = 0
local h2 = 0
local h3 = 0

local R = {
	7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
	5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
	4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
	6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
}

local K = {
	0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
	0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
	0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
	0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
	0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
	0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
	0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
	0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
	0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
	0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
	0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
	0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
	0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
	0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
	0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
	0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391,
}

local function leftRotate(x, c)
	return ((x << c) | (x >> (32 - c))) & 0xffffffff
end

local function allocateZeroed(length)
	local arr = {}
	for i = 0, length - 1 do
		arr[i] = 0
	end
	return arr
end

local function md5(initialMsg, initialLen)
	local len = initialLen or #initialMsg

	h0 = 0x67452301
	h1 = 0xefcdab89
	h2 = 0x98badcfe
	h3 = 0x10325476

	local newLen = (((math.floor((len + 8) / 64) + 1) * 64) - 8)
	local msg = allocateZeroed(newLen + 64)

	for i = 0, len - 1 do
		msg[i] = initialMsg[i] & 0xff
	end

	msg[len] = 0x80

	local bitsLen = (len * 8) & 0xffffffff
	msg[newLen] = bitsLen & 0xff
	msg[newLen + 1] = (bitsLen >> 8) & 0xff
	msg[newLen + 2] = (bitsLen >> 16) & 0xff
	msg[newLen + 3] = (bitsLen >> 24) & 0xff

	for offset = 0, newLen - 1, 64 do
		local w = {}

		for j = 0, 15 do
			local base = offset + j * 4
			w[j] = (
				msg[base] |
				((msg[base + 1] or 0) << 8) |
				((msg[base + 2] or 0) << 16) |
				((msg[base + 3] or 0) << 24)
			) & 0xffffffff
		end

		local a = h0
		local b = h1
		local c = h2
		local d = h3

		for k = 0, 63 do
			local f, g
			if k < 16 then
				f = (b & c) | ((~b) & d)
				g = k
			elseif k < 32 then
				f = (d & b) | ((~d) & c)
				g = (5 * k + 1) % 16
			elseif k < 48 then
				f = b ~ c ~ d
				g = (3 * k + 5) % 16
			else
				f = c ~ (b | (~d))
				g = (7 * k) % 16
			end

			f = f & 0xffffffff

			local temp = d
			d = c
			c = b

			local rotateInput = (a + f + K[k + 1] + w[g]) & 0xffffffff
			b = (b + leftRotate(rotateInput, R[k + 1])) & 0xffffffff
			a = temp
		end

		h0 = (h0 + a) & 0xffffffff
		h1 = (h1 + b) & 0xffffffff
		h2 = (h2 + c) & 0xffffffff
		h3 = (h3 + d) & 0xffffffff
	end
end

local function benchmark()
	local len = MSG_SIZE
	local sf = SCALE_FACTOR

	for _ = 1, sf do
		local msg = {}
		for i = 0, len - 1 do
			msg[i] = i & 0xff
		end
		md5(msg, len)
	end

	local digest = (h0 ~ h1 ~ h2 ~ h3) & 0xffffffff
	return digest == RESULT
end

return benchmark()
