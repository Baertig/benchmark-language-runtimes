-- Lua port of the tarfind benchmark from the provided Python version
-- Simulates searching for filenames within a TAR-like archive header list.

-- Constants mirroring the Python version
local LOCAL_SCALE_FACTOR = 46
local ARCHIVE_FILES = 35
local N_SEARCHES = 5
local GLOBAL_SCALE_FACTOR = 1

local function gen_random_filename(length)
  -- Random uppercase A-Z string of given length (but using the RNG above)
  local t = {}
  for i = 1, length do
    t[i] = string.char((math.random(0,25)) + 65)
  end
  return table.concat(t)
end

local function new_tar_header()
  return {
    filename = "",
    mode = "",
    uID = "",
    gID = "",
    size = "",
    mtime = "",
    checksum = "",
    isLink = "",
    linkedFile = ""
  }
end

local function benchmark_body(lsf, gsf)
  local found = 0

  for _ = 1, lsf do
    for _ = 1, gsf do
      local files = ARCHIVE_FILES
      local hdr = {}

      for i = 0, files do
        local c = new_tar_header()
        local flen = 5 + ((i) % 94) 
        c.isLink = "0"
        c.filename = gen_random_filename(flen)
        c.size = "0"
        hdr[i + 1] = c -- lua list index starts at 1
      end

      found = 0 -- number of times a file was found

      -- Perform N_SEARCHES lookups
      for p = 0, N_SEARCHES - 1 do
        -- choose the position of the file to search for from the mid of the list
        local mid = math.floor(ARCHIVE_FILES / 2)
        local idx0 = (p + mid) % ARCHIVE_FILES      -- 0-based index
        local search = hdr[idx0 + 1].filename       -- convert to 1-based

        -- iterate through all files until found
        for i = 1, files do
          local cur = hdr[i]

          if cur.filename == search then
            found = found + 1
            break
          end
        end
      end
    end
  end

  return (found == N_SEARCHES) 
end


local function benchmark()
  return benchmark_body(LOCAL_SCALE_FACTOR, GLOBAL_SCALE_FACTOR)
end

return benchmark()
