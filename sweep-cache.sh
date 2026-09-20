#!/bin/bash
# VectorBoundary L2 evidence: cache behavior per (cache profile, schedule).
# QEMU cache plugin, LRU, 64B lines. Differential A/B isolates decode.
# Counts are timing-independent; safe to run concurrently with other sweeps.
set -u
QEMU=/usr/local/bin/qemu-riscv64-plugins
CACHE=/tools/libcache.so
BIN=/work/build-riscv/bin
BIN_NR=/work/build-riscv-norepack/bin
MODEL=${MODEL:-/models/SmolLM2-135M-Instruct-Q4_0.gguf}
OUT=${OUT:-/tools/cache-qemu.csv}
VLEN=${VLEN:-256}
P_SHORT="The capital of France is"

if [ ! -f "$OUT" ]; then
    echo "vlen,l1d,l2,schedule,run,n_gen,dmem_accesses,l1d_misses,l2_misses" > "$OUT"
fi

run_one() {
    local l1d="$1" l2="$2" sched="$3" tag="$4" ngen="$5"
    local bin=$BIN envs=""
    if [ "$sched" = "norepack" ]; then bin=$BIN_NR; fi
    if [ "$sched" != "norepack" ] && [ "$sched" != "default" ]; then envs="-E GGML_RVV_SCHEDULE=$sched"; fi
    rm -f /tmp/cache_out.txt
    timeout 7200 $QEMU -L /usr/riscv64-linux-gnu \
        -cpu max,vlen=$VLEN,elen=64,vext_spec=v1.0 \
        -E LD_LIBRARY_PATH=$bin $envs \
        -plugin $CACHE,dcachesize=$l1d,dassoc=8,dblksize=64,icachesize=32768,iassoc=8,iblksize=64,l2=on,l2cachesize=$l2,l2assoc=16,l2blksize=64,evict=lru \
        -d plugin -D /tmp/cache_out.txt \
        $bin/llama-completion -m "$MODEL" -p "$P_SHORT" -n $ngen \
        -t 1 -st --ignore-eos --temp 0 --no-warmup --seed 42 > /tmp/gen.log 2>&1
    local line acc mis l2m
    line=$(grep -A1 "^core #, data accesses" /tmp/cache_out.txt | sed -n '2p')
    acc=$(echo "$line" | awk '{print $2}')
    mis=$(echo "$line" | awk '{print $3}')
    l2m=$(echo "$line" | awk '{print $9}')
    echo "$VLEN,$l1d,$l2,$sched,$tag,$ngen,${acc:-?},${mis:-?},${l2m:-?}" >> "$OUT"
    echo "    $tag l1d=$l1d l2=$l2: acc=${acc:-?} l1dmiss=${mis:-?} l2miss=${l2m:-?}"
}

SCHEDULES=${SCHEDULES:-"norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"}
CACHECFG=${CACHECFG:-"32768:524288 131072:2097152"}
for cfg in $CACHECFG; do
    l1d=${cfg%%:*}; l2=${cfg##*:}
    for sched in $SCHEDULES; do
        echo ">>> l1d=$l1d l2=$l2 sched=$sched"
        run_one $l1d $l2 "$sched" A 1
        run_one $l1d $l2 "$sched" B 9
    done
done
echo "done -> $OUT"
