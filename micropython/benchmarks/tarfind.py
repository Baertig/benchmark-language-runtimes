# import micropython

SCALE_FACTOR = 1
ARCHIVE_FILES = 35
N_SEARCHES = 5

seed = 0

# The port to RIOT does include the module for random (i.e. MICROPY_PY_URANDOM is not defines)
# See the configuration here: https://github.com/kaspar030/micropython/blob/add_riot_port/ports/riot/mpconfigport.h


def randint():
    global seed
    seed = (seed * 1103515245 + 12345) & (1 << 31)
    return seed >> 16


class TarHeader:
    def __init__(self):
        self.filename = ""
        self.mode = ""
        self.uID = ""
        self.gID = ""
        self.size = ""
        self.mtime = ""
        self.checksum = ""
        self.isLink = ""
        self.linkedFile = ""


def _gen_random_filename(length):
    # Random uppercase A-Z string of given length
    return "".join(chr(randint() % 26 + 65) for _ in range(length))


def benchmark():
    sf = SCALE_FACTOR
    found = 0

    for _ in range(sf):
        # Create archive with ARCHIVE_FILES headers
        files = ARCHIVE_FILES
        hdr = [TarHeader() for _ in range(files)]

        for i in range(files):
            c = hdr[i]
            flen = 5 + (i % 94)  # vary file lengths
            c.isLink = "0"
            c.filename = _gen_random_filename(flen)
            c.size = "0"

        found = 0  # number of times a file was found

        # Perform N_SEARCHES lookups
        for p in range(N_SEARCHES):
            # choose the position of the file to search for from the mid of the list
            search = hdr[(p + ARCHIVE_FILES // 2) % ARCHIVE_FILES].filename

            # iterate through all files until found
            for i in range(files):
                cur = hdr[i]

                if cur.filename == search:
                    found += 1
                    break

        # print("")
        # micropython.mem_info()

    return found == N_SEARCHES
