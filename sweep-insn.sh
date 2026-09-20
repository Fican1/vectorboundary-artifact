#!/bin/bash
# VectorBoundary Tier-1 benchmark: exact dynamic instruction counts per
# (VLEN, schedule) via the insn_rvv TCG plugin. Differential methodology:
#   A: short prompt, -n 1   B: short prompt, -n 1+T   C: long prompt, -n 1
#   decode cost = (B-A)/T per token, prefill cost = (C-A)/dP per token.
# Single thread for determinism (threadpool spin-waits are not deterministic).
set -u
QEMU=${QEMU:-/usr/local/bin/qemu-riscv64-plugins}
PLUGIN=${PLUGIN:-/tools/libinsn_rvv.so}
BIN=/work/build-riscv/bin
BIN_NR=/work/build-riscv-norepack/bin
MODEL=${MODEL:-/models/SmolLM2-135M-Instruct-Q4_0.gguf}
OUT=${OUT:-/tools/insn-qemu.csv}
T_DEC=${T_DEC:-8}
P_SHORT="The capital of France is"
P_LONG="one one one one one one one one one one one one one one one one one one one one one one one one one one one one one one one one The capital of France is"

if [ ! -f "$OUT" ]; then
    echo "vlen,schedule,run,n_prompt,n_gen,insns_total,v_arith,vsetvl,v_load,v_store" > "$OUT"
fi

run_one() {
    local vlen="$1" sched="$2" tag="$3" prompt="$4" ngen="$5"
    local bin=$BIN envs=""
    if [ "$sched" = "norepack" ]; then bin=$BIN_NR; fi
    if [ "$sched" != "norepack" ] && [ "$sched" != "default" ]; then envs="-E GGML_RVV_SCHEDULE=$sched"; fi
    rm -f /tmp/counts.txt
    timeout ${TIMEOUT:-3600} $QEMU -L /usr/riscv64-linux-gnu \
        -cpu max,vlen=$vlen,elen=64,vext_spec=v1.0 \
        -E LD_LIBRARY_PATH=$bin $envs \
        -plugin $PLUGIN -d plugin -D /tmp/counts.txt \
        $bin/llama-completion -m "$MODEL" -p "$prompt" -n $ngen \
        -t 1 -st --ignore-eos --temp 0 --no-warmup --seed 42 > /tmp/gen.log 2>&1
    local np
    np=$(grep -oE "prompt eval time.*/ +[0-9]+ tokens" /tmp/gen.log | grep -oE "[0-9]+ tokens" | grep -oE "[0-9]+")
    local vals
    vals=$(awk -F': ' '/^(insns_total|v_arith|vsetvl|v_load|v_store):/{printf "%s,", $2}' /tmp/counts.txt | sed 's/,$//')
    echo "$vlen,$sched,$tag,${np:-?},$ngen,$vals" >> "$OUT"
    echo "    $tag: np=${np:-?} n=$ngen [$vals]"
}

VLENS=${VLENS:-128 256 512 1024}
for vlen in $VLENS; do
    case $vlen in
        128)  SCHEDS=${SCHEDULES:-"norepack q4_0_8x1 q4_0_8x8"};;
        256)  SCHEDS=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"};;
        512)  SCHEDS=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_32x1"};;
        1024) SCHEDS=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_32x1 q4_0_64x1"};;
    esac
    for sched in $SCHEDS; do
        echo ">>> vlen=$vlen sched=$sched"
        run_one $vlen "$sched" A "$P_SHORT" 1
        run_one $vlen "$sched" B "$P_SHORT" $((T_DEC + 1))
        run_one $vlen "$sched" C "$P_LONG" 1
    done
done
echo "done -> $OUT"
