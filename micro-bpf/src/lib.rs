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
use alloc::vec;
use alloc::collections::BTreeMap;
use alloc::boxed::Box;

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

const ITERATIONS_STR: &str = env!("ITERATIONS");

#[cfg(feature = "jit")]
#[repr(C, align(4))]
struct AlignedBuffer([u8; JIT_MEMORY_BUFF_SIZE]);

#[cfg(feature = "jit")]
const JIT_MEMORY_BUFF_SIZE: usize = 20 * 1024;

fn main() {
    let prog: &[u8] = if cfg!(feature = "jit") {
        include_bytes!("../benchmark.o")
    } else {
        include_bytes!("../benchmark.bin")
    };

    let micro_sec = Clock::usec();
    let iterations: usize = ITERATIONS_STR.parse().expect("Failed to parse ITERATIONS");

    // Sleep a bit to wait for the serial to be ready
    micro_sec.sleep(Ticks::from_duration(core::time::Duration::from_secs(3)).
            expect("5 would only overflow a nanosecond timer"));

    println!("=== Benchmark Begins ===");
    println!("iteration;init_runtime_us;load_program_us;execution_time_us;correct");

    for i in 0..iterations {
        print!("{};", i);
        print!("0;"); // init runtime not applicable here

        let mut vm: Option<EbpfVmMbuff> = None;

        #[cfg(feature = "jit")]
        let mut jitted_fn: Option<unsafe fn(*mut u8, usize, *mut u8, usize) -> u32> = None;

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
                #[cfg(not(feature = "jit"))]
                {
                    vm = Some(
                        EbpfVmMbuff::new(Some(prog), rbpf::InterpreterVariant::FemtoContainersHeader)
                            .expect("failed to load program"),
                    );
                    register_all(vm.as_mut().unwrap());
                    vm.as_ref().unwrap().verify_loaded_program().expect("program verification failed");
                }

                #[cfg(feature = "jit")]
                {
                    use crate::middleware::ALL_HELPERS;

                    let mut prog_vec = prog.to_vec();

                    let mut helpers_map = BTreeMap::new();
                    for h in ALL_HELPERS.iter() {
                        helpers_map.insert(h.id as u32, h.function);
                    }

                    // Allocate the aligned buffer
                    let mut jit_memory_buff = Box::new(AlignedBuffer([0; JIT_MEMORY_BUFF_SIZE]));

                    println!("JIT compiling...");

                    let jit = rbpf::JitMemory::new(&mut prog_vec, &mut jit_memory_buff.0, &helpers_map, false, false, rbpf::InterpreterVariant::RawObjectFile).expect("Failed jit compile");

                    let offset = jit.text_offset.clone();

                    jitted_fn = Some(rbpf::JitMemory::get_prog_from_slice(
                            &jit_memory_buff.0,
                            offset,
                        ));

                    println!("JIT compilation done.");
                }
            })
            .expect("failed to measure load program time");

        print!("{};", load_program_duration.0);

        let mut res = false;

        let execution_duration = micro_sec
            .time(|| {
                #[cfg(not(feature = "jit"))]
                {
                    let vm = vm.unwrap();
                    let allowed_memory_regions: Vec<(u64, u64)> = Vec::new();

                    res = vm
                        .execute_program(mem, &[], allowed_memory_regions)
                        .expect("programm execution failed")
                        == 1;

                }
                
                #[cfg(feature = "jit")]
                {
                    println!("Executing JITted code");
                    // Sleep is needed sometimes, because when the execution fails no output is displayed otherwise.
                    micro_sec.sleep(Ticks::from_duration(core::time::Duration::from_secs(3)).
                        expect("5 would only overflow a nanosecond timer"));

                    res = unsafe {
                        jitted_fn.unwrap()(0 as *mut u8, 0, 0 as *mut u8, 0)
                    } == 1;

                    println!("JITted code execution done.");
                }
            })
            .expect("failed to measure execution time");

        print!("{};", execution_duration.0);
        print!("{}\n", res.to_string());
    }

    println!("=== Benchmark End ===");
}
