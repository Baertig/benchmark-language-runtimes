fn main() {
    println!("cargo:rerun-if-env-changed=ITERATIONS");
    let iterations = std::env::var("ITERATIONS").expect("ITERATIONS not set");
    println!("cargo:rustc-env=ITERATIONS={}", iterations);
}
