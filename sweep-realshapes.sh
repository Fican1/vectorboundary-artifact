#!/bin/bash
# Skeptic check: does the deployed model still hit oracle on REAL LLM
# weight shapes (576-4864), which are all outside the 32-512 training grid?
set -u
QEMU=/usr/local/bin/qemu-riscv64-plugins
PLUGIN=/tools/libinsn_rvv.so
BIN=/work/build-riscv/bin
OUT=${OUT:-/tools/realshapes-qemu.csv}
VLEN=${VLEN:-256}
TYPE=q4_0

if [ ! -f "$OUT" ]; then
    echo "type,vlen,N,K,M,schedule,reps,insns_total" > "$OUT"
fi

run_one() {
    local n="$1" k="$2" m="$3" sched="$4" reps="$5"
    local envs="" extra=""
    if [ "$sched" = "norepack" ]; then extra="--no-repack"
    elif [ "$sched" != "default" ]; then envs="-E GGML_RVV_SCHEDULE=$sched"; fi
    rm -f /tmp/counts.txt
    timeout 600 $QEMU -L /usr/riscv64-linux-gnu \
        -cpu max,vlen=$VLEN,elen=64,vext_spec=v1.0 \
        -E LD_LIBRARY_PATH=$BIN $envs \
        -plugin $PLUGIN -d plugin -D /tmp/counts.txt \
        $BIN/vb-shape-bench $TYPE $n $k $m $reps $extra > /dev/null 2>&1
    local tot
    tot=$(awk -F': ' '/^insns_total:/{print $2}' /tmp/counts.txt)
    echo "$TYPE,$VLEN,$n,$k,$m,$sched,$reps,${tot:-0}" >> "$OUT"
}

# real (N,K) pairs from the four benchmark models: hidden-hidden and ffn-up
SHAPES=${SHAPES:-"576:576 1536:576 960:960 2560:960 896:896 4864:896 1024:1024 3072:1024"}
SCHEDULES=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"}
for nk in $SHAPES; do
    n=${nk%%:*}; k=${nk##*:}
    for sched in $SCHEDULES; do
        for m in 1 32; do
            run_one $n $k $m "$sched" 2
            run_one $n $k $m "$sched" 10
        done
    done
    echo "done: N=$n K=$k"
done
echo "done -> $OUT"
