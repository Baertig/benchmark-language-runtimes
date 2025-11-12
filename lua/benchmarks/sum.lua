local SCALE_FACTOR = 100

local sum = 0
for i = 0, SCALE_FACTOR do
    sum = sum + i
end

local expectedSum = (SCALE_FACTOR * (SCALE_FACTOR + 1)) // 2

return sum == expectedSum 