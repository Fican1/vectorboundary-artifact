#!/bin/bash
# VectorBoundary: functional validation of the RVV schedule registry under QEMU.
# Greedy llama-simple output must be identical across VLENs and forced
# schedules, and must match the no-repack reference build.
set -u
BIN=/work/build-riscv/bin
BIN_NR=/work/build-riscv-norepack/bin
MODEL=/models/SmolLM2-135M-Instruct-Q4_0.gguf
PROMPT="The capital of France is"

run_case() {
    local tag="$1" vlen="$2" sched="$3" bin="$4"
    local cmd="qemu-riscv64 -L /usr/riscv64-linux-gnu -cpu max,vlen=$vlen,elen=64,vext_spec=v1.0 -E LD_LIBRARY_PATH=$bin"
    if [ -n "$sched" ]; then cmd="$cmd -E GGML_RVV_SCHEDULE=$sched"; fi
    local out
    out=$(timeout 1800 $cmd $bin/llama-simple -m $MODEL -n 8 "$PROMPT" 2>/tmp/err.log)
    echo "== $tag | vlen=$vlen sched=${sched:-default}"
    echo "   text: $out"
    grep -E "GGML_RVV_SCHEDULE" /tmp/err.log | head -1 | sed 's/^/   log: /'
}

echo "### reference: repack disabled at build time"
if [ -x $BIN_NR/llama-simple ]; then
    run_case "ref-norepack" 256 "" $BIN_NR
else
    echo "   (no-repack build missing, skipped)"
fi
echo
echo "### default schedule per VLEN"
for v in 128 256 512 1024; do run_case "default-v$v" $v "" $BIN; done
echo
echo "### forced schedules"
run_case "force-8x1-v256"  256 "q4_0_8x1"  $BIN
run_case "force-8x8-v256"  256 "q4_0_8x8"  $BIN
run_case "force-16x1-v256" 256 "q4_0_16x1" $BIN
run_case "force-8x1-v512"  512 "q4_0_8x1"  $BIN
run_case "force-8x8-v512"  512 "q4_0_8x8"  $BIN
echo
echo "### illegal force (q4_0_64x1 needs vlenb=128) at vlen=256 -> falls back to un-repacked"
run_case "force-illegal-v256" 256 "q4_0_64x1" $BIN
