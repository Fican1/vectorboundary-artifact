#!/bin/bash
# VectorBoundary boundary curve: decode instructions per token vs batch size.
# llama-batched-bench with npl parallel sequences; ntg 1 vs 9 differential
# isolates npl*8 decode tokens executed at batch width npl.
set -u
QEMU=/usr/local/bin/qemu-riscv64-plugins
PLUGIN=/tools/libinsn_rvv.so
BIN=/work/build-riscv/bin
BIN_NR=/work/build-riscv-norepack/bin
MODEL=${MODEL:-/models/SmolLM2-135M-Instruct-Q4_0.gguf}
OUT=${OUT:-/tools/batch-qemu.csv}
VLEN=${VLEN:-256}
NPP=${NPP:-32}

if [ ! -f "$OUT" ]; then
    echo "vlen,schedule,npl,ntg,insns_total,v_arith,vsetvl,v_load,v_store" > "$OUT"
fi

run_one() {
    local sched="$1" npl="$2" ntg="$3"
    local bin=$BIN envs=""
    if [ "$sched" = "norepack" ]; then bin=$BIN_NR; fi
    if [ "$sched" != "norepack" ] && [ "$sched" != "default" ]; then envs="-E GGML_RVV_SCHEDULE=$sched"; fi
    rm -f /tmp/counts.txt
    timeout 7200 $QEMU -L /usr/riscv64-linux-gnu \
        -cpu max,vlen=$VLEN,elen=64,vext_spec=v1.0 \
        -E LD_LIBRARY_PATH=$bin $envs \
        -plugin $PLUGIN -d plugin -D /tmp/counts.txt \
        $bin/llama-batched-bench -m "$MODEL" -c 2048 -b 512 -ub 512 \
        -npp $NPP -ntg $ntg -npl $npl -t 1 > /tmp/gen.log 2>&1
    local vals
    vals=$(awk -F': ' '/^(insns_total|v_arith|vsetvl|v_load|v_store):/{printf "%s,", $2}' /tmp/counts.txt | sed 's/,$//')
    echo "$VLEN,$sched,$npl,$ntg,$vals" >> "$OUT"
    echo "    npl=$npl ntg=$ntg [$vals]"
}

SCHEDULES=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"}
NPLS=${NPLS:-"1 2 4 8"}
for sched in $SCHEDULES; do
    for npl in $NPLS; do
        echo ">>> sched=$sched npl=$npl"
        run_one "$sched" $npl 1
        run_one "$sched" $npl 9
    done
done
echo "done -> $OUT"
