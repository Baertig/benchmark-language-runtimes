#ifndef SUPPORT_H
#define SUPPORT_H

/* Every benchmark implements this as its entry point. Don't allow it to be
   inlined! */

int benchmark (void) __attribute__ ((noinline));

#endif