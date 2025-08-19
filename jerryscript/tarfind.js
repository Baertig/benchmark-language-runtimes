/**
 * JavaScript port of the tarfind benchmark from C/Python.
 * Simulates searching for filenames within a TAR-like archive header list.
 */

var ARCHIVE_FILES = 35;
var N_SEARCHES = 5;
var LOCAL_SCALE_FACTOR = 46;
var GLOBAL_SCALE_FACTOR = 1;

var seed = 0;

function randint() {
  seed = (seed * 1103515245 + 12345) & ((1 << 31) - 1);
  return seed >> 16;
}

function TarHeader() {
  this.filename = "";
  this.mode = "";
  this.uID = "";
  this.gID = "";
  this.size = "";
  this.mtime = "";
  this.checksum = "";
  this.isLink = "";
  this.linkedFile = "";
}

var CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

function _gen_random_filename(length) {
  // Random uppercase A-Z string of given length
  var result = "";
  for (var i = 0; i < length; i++) {
    result += CHARS[randint() % 26];
  }
  return result;
}

function benchmark_body(lsf, gsf) {
  var found = 0;

  for (var outer = 0; outer < lsf; outer++) {
    for (var inner = 0; inner < gsf; inner++) {
      // Create archive with ARCHIVE_FILES headers
      var files = ARCHIVE_FILES;
      var hdr = [];

      for (var i = 0; i < files; i++) {
        hdr[i] = new TarHeader();
      }

      for (var i = 0; i < files; i++) {
        var c = hdr[i];
        var flen = 5 + (i % 94); // vary file lengths
        c.isLink = "0";
        c.filename = _gen_random_filename(flen);
        c.size = "0";
      }

      found = 0; // number of times a file was found

      // Perform N_SEARCHES lookups
      for (var p = 0; p < N_SEARCHES; p++) {
        // choose the position of the file to search for from the mid of the list
        var search =
          hdr[(p + ((ARCHIVE_FILES / 2) | 0)) % ARCHIVE_FILES].filename; // -> little js hack, because jerryscript does not support Math.floor, we just use | 0 instead -> converts a float number to a integer.

        // iterate through all files until found
        for (var i = 0; i < files; i++) {
          var cur = hdr[i];

          if (cur.filename === search) {
            found += 1;
            break;
          }
        }
      }
    }
  }

  return found === N_SEARCHES;
}

function benchmark() {
  return benchmark_body(LOCAL_SCALE_FACTOR, GLOBAL_SCALE_FACTOR);
}

//jerryscript automatically returns the value of the last expression
benchmark();
