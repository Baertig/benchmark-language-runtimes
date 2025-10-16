/*
 * This benchmark simulates the search in a TAR archive
 * for a set of filenames
 *
 * Created by Julian Kunkel for Embench-iot
 * Licensed under MIT
 */
// SPDX-License-Identifier: MIT
// #include <stdio.h>
// #include <stdlib.h>
// #include <string.h>
#include <stdint.h>

// definitions come from RIOT/build/pkg/wamr/core/iwasm/libraries/libc-builtin/libc_builtin_wrapper.c 
// search for wrapper_<function> and remove the first argument
// --> At the bottom of the file they are registered
extern uint32_t memset(void *s, int32_t c, uint32_t size);
extern int printf(const char *, ...);
extern uint32_t malloc(uint32_t size);
extern void free(void *ptr);
/* rand is provided by host (registered native) */
extern int rand(void);


#include "support.h"

#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif

// number of files in the archive
#define ARCHIVE_FILES 35

#define N_SEARCHES 5

// this is the basic TAR header format which is in ASCII
typedef struct {
  char filename[100];
  char mode[8];  // file mode
  char uID[8];   // user id
  char gID[8];   // group id
  char size[12]; // in bytes octal base
  char mtime[12]; // numeric Unix time format (octal)
  char checksum[8]; // for the header, ignored herew2
  char isLink;
  char linkedFile[100];
} tar_header_t;



int __attribute__ ((noinline))
benchmark()
{
  int i, p;
  tar_header_t * hdr;
  int found;
  unsigned int sf = SCALE_FACTOR;

  for (unsigned int sf_cnt = 0; sf_cnt < sf; sf_cnt++) {
    // always create ARCHIVE_FILES files in the archive
    int files = ARCHIVE_FILES;
    hdr = (void*) malloc(sizeof(tar_header_t) * files);
    for (i = 0; i < files; i++){
      // create record
      tar_header_t * c = & hdr[i];
      // initialize here for cache efficiency reasons
      memset(c, 0, sizeof(tar_header_t));
      int flen = 5 + i % 94; // vary file lengths
      c->isLink = '0';
      for(p = 0; p < flen; p++){
        c->filename[p] = rand() % 26 + 65;
      }
      c->size[0] = '0';
    }

    found = 0; // number of times a file was found
    // actual benchmark, strcmp with a set of N_SEARCHES files
    // the memory access here is chosen inefficiently on purpose
    for (p = 0; p < N_SEARCHES; p++){
      // chose the position of the file to search for from the mid of the list
      char * search = hdr[(p + ARCHIVE_FILES/2) % ARCHIVE_FILES].filename;

      // for each filename iterate through all files until found
      for (i = 0; i < files; i++){
        tar_header_t * cur = & hdr[i];
        // implementation of strcmp
        char *c1;
        char *c2;
        for (c1 = hdr[i].filename, c2 = search; (*c1 != '\0' && *c2 != '\0' && *c1 == *c2) ; c1++, c2++);
        // complete match?
        if(*c1 == '\0' && *c2 == '\0'){
          found++;
          break;
        }
      }
    }
    free(hdr);
  }

  return found == N_SEARCHES;
}