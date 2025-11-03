// SPDX-FileCopyrightText: 2020 Christian Amsüss
// SPDX-License-Identifier: LGPL-2.1-only
#![no_std]

mod infra;
mod middleware;
mod util;

use alloc::string::ToString;
use rbpf::EbpfVmMbuff;
use riot_wrappers::ztimer::{Clock, Ticks};
use riot_wrappers::{println, riot_main};

extern crate alloc;
extern crate riot_sys;
extern crate rust_riotmodules;

use alloc::vec::Vec;

use crate::middleware::helpers::register_all;

#[macro_export]
macro_rules! print {
    ( $( $arg:expr ),* ) => {{
        use core::fmt::Write;
        use riot_wrappers::stdio::Stdio;
        let _ = write!(Stdio {}, $( $arg, )* );
    }}
}

riot_main!(main);

#[cfg(feature = "libud")]
#[repr(C)]
struct Context {
    a: [[i64; 20]; 20],
    b: [i64; 20],
    x: [i64; 20],
    y: [i64; 100],
}

fn main() {
    let prog = include_bytes!("../benchmark.bin");
    println!("Hello Rust!");
    let micro_sec = Clock::usec();

    println!("=== Benchmark Begins ===");
    println!("iteration;init_runtime_us;load_program_us;execution_time_us;correct");
    // 5 iterations
    for iteration in 0..5 {
        print!("{};", iteration);
        print!("0;"); // init runtime not applicable here

        let mut vm: Option<EbpfVmMbuff> = None;

        #[cfg(feature = "libud")]
        let ctx = Context {
            a: [[0; 20]; 20], // Initialize as needed
            b: [0; 20],
            x: [0; 20],
            y: [0; 100],
        };

        #[cfg(feature = "libud")]
        let mem = unsafe {
            core::slice::from_raw_parts(
                &ctx as *const Context as *const u8,
                core::mem::size_of::<Context>(),
            )
        };

        #[cfg(not(feature = "libud"))]
        let mem: &[u8] = &[]; // Default empty slice if not libud

        let load_program_duration = micro_sec
            .time(|| {
                vm = Some(
                    EbpfVmMbuff::new(Some(prog), rbpf::InterpreterVariant::FemtoContainersHeader)
                        .expect("failed to load program"),
                );
                register_all(vm.as_mut().unwrap());
            })
            .expect("failed to measure load program time");

        print!("{};", load_program_duration.0);

        let vm = vm.unwrap();
        let allowed_memory_regions: Vec<(u64, u64)> = Vec::new();
        let mut res = false;

        let execution_duration = micro_sec
            .time(|| {
                res = vm
                    .execute_program(mem, &[], allowed_memory_regions)
                    .unwrap()
                    == 1;
            })
            .expect("failed to measure execution time");

        print!("{};", execution_duration.0);
        print!("{}\n", res.to_string());
    }

    println!("=== Benchmark End ===");
}
