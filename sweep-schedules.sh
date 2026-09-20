#!/bin/bash
# VectorBoundary: sweep (VLEN x schedule) with llama-bench, append CSV rows.
# Under QEMU the timings are NOT real RVV performance - they only validate the
# pipeline. Run the same script on real hardware for usable numbers.
#
# env: VLENS="128 256 512 1024"  SCHEDULES="default norepack q4_0_8x1 ..."
#      NPP=32 NTG=8 REPS=1 THREADS=2 OUT=/tools/sweep.csv
set -u
BIN=/work/build-riscv/bin
BIN_NR=/work/build-riscv-norepack/bin
MODEL=${MODEL:-/models/SmolLM2-135M-Instruct-Q4_0.gguf}
VLENS=${VLENS:-256}
SCHEDULES=${SCHEDULES:-default norepack q4_0_8x1 q4_0_8x8}
NPP=${NPP:-32}
NTG=${NTG:-8}
REPS=${REPS:-1}
THREADS=${THREADS:-2}
OUT=${OUT:-/tools/sweep-qemu.csv}

if [ ! -f "$OUT" ]; then
    echo "host,vlen,schedule,test,t_per_s,model,n_threads" > "$OUT"
fi

for vlen in $VLENS; do
    for sched in $SCHEDULES; do
        bin=$BIN
        envs="-E LD_LIBRARY_PATH=$BIN"
        if [ "$sched" = "norepack" ]; then
            bin=$BIN_NR
            envs="-E LD_LIBRARY_PATH=$BIN_NR"
        elif [ "$sched" != "default" ]; then
            envs="$envs -E GGML_RVV_SCHEDULE=$sched"
        fi
        echo ">>> vlen=$vlen sched=$sched"
        res=$(timeout 3600 qemu-riscv64 -L /usr/riscv64-linux-gnu \
            -cpu max,vlen=$vlen,elen=64,vext_spec=v1.0 $envs \
            $bin/llama-bench -m "$MODEL" -p $NPP -n $NTG -r $REPS -t $THREADS -o csv 2>/dev/null)
        # llama-bench csv trailing columns: n_prompt,n_gen,n_depth,test_time,avg_ns,stddev_ns,avg_ts,stddev_ts
        echo "$res" | tail -n +2 | while IFS=',' read -r -a f; do
            ncol=${#f[@]}
            n_prompt=$(echo "${f[$((ncol-8))]}" | tr -d '"')
            n_gen=$(echo "${f[$((ncol-7))]}" | tr -d '"')
            avg_ts=$(echo "${f[$((ncol-2))]}" | tr -d '"')
            if [ "$n_gen" = "0" ]; then test_name="pp$n_prompt"; else test_name="tg$n_gen"; fi
            echo "qemu,$vlen,$sched,$test_name,$avg_ts,$(basename $MODEL),$THREADS" >> "$OUT"
        done
        tail -2 "$OUT" | sed 's/^/    /'
    done
done
echo "done -> $OUT"
