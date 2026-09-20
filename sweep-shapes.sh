#!/bin/bash
# VectorBoundary: kernel-level shape sweep (Peccia-aligned square grid + M=1
# decode-like column) via vb-shape-bench under the insn plugin.
# Differential reps 2 vs 10 isolates 8 matmul executions.
set -u
QEMU=/usr/local/bin/qemu-riscv64-plugins
PLUGIN=/tools/libinsn_rvv.so
BIN=/work/build-riscv/bin
OUT=${OUT:-/tools/shapes-qemu.csv}
VLEN=${VLEN:-256}
TYPE=${TYPE:-q4_0}

if [ ! -f "$OUT" ]; then
    echo "type,vlen,N,K,M,schedule,reps,insns_total,v_arith,vsetvl,v_load,v_store" > "$OUT"
fi

run_one() {
    local n="$1" k="$2" m="$3" sched="$4" reps="$5"
    local envs="" extra=""
    if [ "$sched" = "norepack" ]; then
        extra="--no-repack"
    elif [ "$sched" != "default" ]; then
        envs="-E GGML_RVV_SCHEDULE=$sched"
    fi
    rm -f /tmp/counts.txt
    timeout 1800 $QEMU -L /usr/riscv64-linux-gnu \
        -cpu max,vlen=$VLEN,elen=64,vext_spec=v1.0 \
        -E LD_LIBRARY_PATH=$BIN $envs \
        -plugin $PLUGIN -d plugin -D /tmp/counts.txt \
        $BIN/vb-shape-bench $TYPE $n $k $m $reps $extra > /dev/null 2>&1
    local vals
    vals=$(awk -F': ' '/^(insns_total|v_arith|vsetvl|v_load|v_store):/{printf "%s,", $2}' /tmp/counts.txt | sed 's/,$//')
    echo "$TYPE,$VLEN,$n,$k,$m,$sched,$reps,$vals" >> "$OUT"
}

SIZES=${SIZES:-"32 64 128 256 512"}
SCHEDULES=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"}
for s in $SIZES; do
    for sched in $SCHEDULES; do
        for m in $s 1; do
            echo ">>> N=K=$s M=$m sched=$sched"
            run_one $s $s $m "$sched" 2
            run_one $s $s $m "$sched" 10
        done
    done
done
echo "done -> $OUT"
