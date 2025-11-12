#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif

int __attribute__ ((noinline)) benchmark() {
    __asm__ volatile (
        // R6 = sum = 0
        "r6 = 0\n\t"    
        
        // R7 = i = 0
        "r7 = 0\n\t"    
        
        // R4 = SCALE_FACTOR (This is loaded as a constant into R4)
        "r4 = %[scale_factor]\n\t"
        
        // --- Loop Start (label .L_loop_start) ---

        // jump back to here if R7 <= R4 (i <= SCALE_FACTOR)
        ".L_loop_start:\n\t"
        
        // Check condition: if R7 > R4 (i > SCALE_FACTOR), jump to .L_loop_end
        // JGT: Jump if Greater Than. 
        // Note: We check the opposite of the loop condition to jump out.
        "if r7 > r4 goto .L_loop_end\n\t"

        // --- Loop Body: sum += i ---

        // R6 = R6 + R7 (sum += i)
        "r6 += r7\n\t"
        
        // --- Increment and Continue ---
        
        // R7 = R7 + 1 (i++)
        "r7 += 1\n\t" 
        
        // Unconditional jump back to the start of the loop: goto .L_loop_start
        "goto .L_loop_start\n\t"

        // --- Loop End (label .L_loop_end) ---
        
        ".L_loop_end:\n\t"

        // --- Calculate and Compare ---
        
        // Calculate Expected Sum: expected_sum = (SCALE_FACTOR * (SCALE_FACTOR + 1)) / 2
        // R2 = SCALE_FACTOR (R4)
        "r2 = r4\n\t"
        
        // R3 = SCALE_FACTOR (R4) + 1
        "r3 = r4\n\t"
        "r3 += 1\n\t" 
        
        // R2 = R2 * R3 (SCALE_FACTOR * (SCALE_FACTOR + 1))
        // Note: Multiplication by a register requires a separate instruction.
        "r2 *= r3\n\t" 
        
        // R2 = R2 / 2 (Divide by 2)
        "r2 /= 2\n\t"
        
        // R0 = 0 (Initialize return value: assume failure)
        "r0 = 0\n\t"
        
        // Check condition: if R6 == R2 (sum == expected_sum), jump to .L_return_success
        "if r6 == r2 goto .L_return_success\n\t"
        
        // If not equal, we fall through and exit with R0 = 0 (already set above)
        "goto .L_exit\n\t"

        // --- Success Return ---
        ".L_return_success:\n\t"
        // R0 = 1 (Set return value to 1 for success)
        "r0 = 1\n\t"

        // --- Exit ---
        
        ".L_exit:\n\t"
        // Return R0
        "exit\n\t" 

        // Output constraint: Pass the C macro value SCALE_FACTOR to the assembly instruction.
        : /* No output variables */
        : [scale_factor] "i" (SCALE_FACTOR)
        : 
    );

    // This return is effectively unreachable but is required to compile the C function signature.
    return 0;
}