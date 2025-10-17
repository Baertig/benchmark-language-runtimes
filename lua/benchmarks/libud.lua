local a = {}
local b = {}
local x = {}
local SCALE_FACTOR = 1

for i = 1, 20 do
    a[i] = {}
end

local function ludcmp(N)
    local y = {}
    local w

    for i = 1, N - 1 do
        for j = i + 1, N do
            w = a[j][i]
            if i > 1 then
                for k = 1, i - 1 do
                    w = w - a[j][k] * a[k][i]
                end
            end
            a[j][i] = math.floor(w / a[i][i])
        end

        for j = i + 1, N do
            w = a[i + 1][j]
            for k = 1, i do
                w = w - a[i + 1][k] * a[k][j]
            end
            a[i + 1][j] = w
        end
    end

    y[1] = b[1]
    for i = 2, N do
        w = b[i]
        for j = 1, i - 1 do
            w = w - a[i][j] * y[j]
        end
        y[i] = w
    end

    x[N] = math.floor(y[N] / a[N][N])
    for i = N - 1, 1, -1 do
        w = y[i]
        for j = i + 1, N do
            w = w - a[i][j] * x[j]
        end
        x[i] = math.floor(w / a[i][i])
    end

    return 0
end

local function verify_benchmark(res)
  
    local x_ref = {0, 0, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

    if res ~= 0 then
        return false
    end

    -- Compare the calculated vector 'x' with the reference 'x_ref'.
    for i = 1, 20 do
        if (x[i] or 0) ~= x_ref[i] then
            return false
        end
    end

    return true
end


local function benchmark()
    -- This scale factor can be changed to equalize the runtime of benchmarks.
    local sf = SCALE_FACTOR
    local chkerr = 0

    for _ = 1, sf do
        local n_c_equivalent = 5
        local matrix_size = n_c_equivalent + 1
        local w

        -- Initialize the 'a' matrix and 'b' vector with test data.
        for i = 1, matrix_size do
            w = 0
            for j = 1, matrix_size do
                a[i][j] = i + j
                if i == j then
                    a[i][j] = a[i][j] * 2
                end
                w = w + a[i][j]
            end
            b[i] = w
        end

        -- Run the LU decomposition.
        chkerr = ludcmp(matrix_size)
    end

    return verify_benchmark(chkerr)
end

return benchmark()
