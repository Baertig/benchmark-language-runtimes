(module
  (func $benchmark (result i32)
    (local $sum i32)
    (local $i i32)
    (local $scale i32)
    (local $expected i32)

    ;; Set SCALE_FACTOR (hardcode or import if needed)
    i32.const {{SCALE_FACTOR}}
    local.set $scale

    ;; Initialize sum to 0
    i32.const 0
    local.set $sum

    ;; Loop: for (i = 0; i <= scale; i++) sum += i
    i32.const 0
    local.set $i
    (loop $loop
      ;; sum += i
      local.get $sum
      local.get $i
      i32.add
      local.set $sum

      ;; i++
      local.get $i
      i32.const 1
      i32.add
      local.set $i

      ;; if i <= scale, continue loop
      local.get $i
      local.get $scale
      i32.le_s
      br_if $loop
    )

    ;; Compute expected_sum = (scale * (scale + 1)) / 2
    local.get $scale
    local.get $scale
    i32.const 1
    i32.add
    i32.mul
    i32.const 2
    i32.div_s
    local.set $expected

    ;; Return (sum == expected) ? 1 : 0
    local.get $sum
    local.get $expected
    i32.eq
    (if (result i32)
      (then i32.const 1)
      (else i32.const 0)
    )
  )
  (export "main" (func $benchmark))
)