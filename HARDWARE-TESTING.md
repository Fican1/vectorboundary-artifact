# Running this on real RVV hardware

Thank you for helping test this. Everything in this repo so far was measured
under QEMU (exact instruction counts, not timing). We need real
tokens/second numbers from actual RVV 1.0 silicon (Banana Pi BPI-F3 / Milk-V
Jupiter / SpacemiT K1-based boards, or anything else with RVV 1.0 and
VLEN>=128) to close that gap. This should take about 15 minutes.

## What you need

- A RISC-V board with RVV 1.0 (`cat /proc/cpuinfo` should show `v` in the
  `isa` line, or check `riscv,isa` in `/proc/device-tree`).
- `gcc` >= 12 and `cmake` >= 3.16 (check with `gcc --version`; if it's older
  than 12 the RVV kernels here may not compile - let us know and we'll sort
  out a cross-compile option instead).
- ~500MB free disk and a working internet connection to fetch a small model.

## Steps

```sh
git clone --branch vectorboundary https://github.com/Fican1/llama.cpp.git
cd llama.cpp

# 1. environment fingerprint - please include this in what you send back
uname -a > /tmp/vb-env.txt
cat /proc/cpuinfo | head -30 >> /tmp/vb-env.txt
gcc --version | head -1 >> /tmp/vb-env.txt

# 2. build
cmake -B build -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
cmake --build build -j"$(nproc)" --target llama-bench llama-completion test-backend-ops

# 3. correctness sanity check first (should say 1323/1323 passed)
./build/bin/test-backend-ops test -b CPU -o MUL_MAT

# 4. a small model to benchmark with
curl -sL -o /tmp/smol-q4_0.gguf \
  "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_0.gguf"

# 5. the actual sweep - runs upstream's rule, our learned dispatcher, and the
#    non-repacked baseline, so we can compare them on your hardware
bash vectorboundary-hw-sweep.sh /tmp/smol-q4_0.gguf   # writes /tmp/vb-hw-results.csv
```

If that script isn't in your checkout (we're adding it - `git pull` first),
run this by hand instead, it does the same thing:

```sh
BIN=./build/bin
MODEL=/tmp/smol-q4_0.gguf
OUT=/tmp/vb-hw-results.csv
echo "config,pp_tok_s,tg_tok_s" > "$OUT"
for cfg in "upstream-heuristic:GGML_RVV_DISPATCH=heuristic" "learned-dispatch:"; do
  name=${cfg%%:*}; env=${cfg#*:}
  res=$(env $env $BIN/llama-bench -m "$MODEL" -p 512 -n 128 -r 3 -o csv 2>/dev/null | tail -n +2)
  echo "$name,$res" >> "$OUT"
done
# non-repacked baseline uses the -nr / --no-repack CLI flag, not an env var
res=$($BIN/llama-bench -m "$MODEL" -p 512 -n 128 -r 3 -nr -o csv 2>/dev/null | tail -n +2)
echo "norepack,$res" >> "$OUT"
cat "$OUT"
```

The two rows that matter most are `upstream-heuristic` vs `learned-dispatch`
- that's the actual comparison this project is about. `norepack` is the
baseline both of them are trying to beat.

## Sending results back

Please open an issue at
**https://github.com/Fican1/vectorboundary-artifact/issues/new** titled
`hardware result: <your board name>` and attach:
- `/tmp/vb-env.txt`
- `/tmp/vb-hw-results.csv`
- the output of step 3 (pass/fail count)

Or, if you're comfortable with git, a PR adding both files under
`results/hardware/<board-name>-<date>/` is even better - then they're
versioned alongside everything else here.

## What this measures and why it matters

The QEMU-only results in this repo show that llama.cpp's upstream RVV
kernel-selection rule reaches only 74-85% of the achievable
instruction-count optimum (see `VectorBoundary-Report.md`), and that a
small learned model closes that gap to 100% on the same axis. Your run is
the first real check of whether that instruction-count advantage survives
on actual silicon, where cache and memory effects QEMU can't model come
into play. Either outcome is useful to us: if the ranking holds, that's the
headline result; if it doesn't, that's exactly the kind of instruction-count
vs.\ real-time mismatch this project's motivation section is already about
(see Finding #2 in the report), and knowing where it breaks is valuable too.
