# VectorBoundary 基准测试协议 (Benchmark Protocol)

版本: 2026-09-15。适用于 `llama.cpp` fork 分支 `vectorboundary`(本地 `e:\AAAI_risc-v\llama.cpp`)上的
RVV repack schedule 研究。所有论文数据必须按本协议采集,并标注证据层级(Tier)。

## 1. 环境固定 (Environment Pinning)

每次实验必须记录以下字段,写入结果 CSV 与实验日志;任一字段变化即视为新实验批次:

| 字段 | 记录方式 | 当前参考值 |
|---|---|---|
| `git_commit` | `git rev-parse HEAD`(分支 `vectorboundary`) | 例: `449f9bde4` |
| `compiler` | 交叉编译器版本 | riscv64 cross gcc 14.2 (Docker 镜像 `vb-riscv2`, debian:trixie) |
| `cflags` | CMake 完整配置命令 + `-march` 串 | 例: `-march=rv64gcv_zvfh` |
| `build_variant` | `repack` / `norepack`(`-DGGML_CPU_REPACK=OFF`) | 两个独立 build 目录 |
| `qemu_version` | `qemu-riscv64 --version` | 10.0.13(必须 >= 10,8.2 缺 `zvfh`) |
| `qemu_cpu` | 完整 `-cpu` 串 | `max,vlen=<V>,elen=64,vext_spec=v1.0` |
| `threads` | `-t` 线程数 | QEMU 下固定 2;真机按核数记录 |
| `governor` | 真机 CPU governor(Tier 3 必填) | `performance`,并记录实测频率 |
| `model` | GGUF 文件名 + sha256 | `SmolLM2-135M-Instruct-Q4_0.gguf` |
| `schedule` | `GGML_RVV_SCHEDULE` 取值或 `default`/`norepack` | 见 §5 基线表 |

## 2. 三层证据体系

### Tier 1 — QEMU 动态指令计数(精确、确定性)

工具:自定义 TCG 插件 `insn_rvv.c`(`vb-tools/insn_rvv.c`),用法:

```sh
qemu-riscv64 -plugin ./libinsn_rvv.so -d plugin -D out.txt \
  -cpu max,vlen=256,elen=64,vext_spec=v1.0 <bin> ...
```

指标(每次执行精确计数):`insns_total`、`v_arith`(OP-V 算术)、`vsetvl`(vsetvl/vsetvli/vsetivli 族)、
`v_load`、`v_store`。

差分法(隔离 decode / prefill 开销,消除加载与运行时噪声):对每个 config(vlen × schedule)——

- Run A:prompt `P`,`-n 1` → 基线(模型加载 + prefill(P) + 1 token)。
- Run B:同一 prompt `P`,`-n 1+T` → `B − A` = 恰好 T 个 decode token 的指令数。
- Run C:更长 prompt `P'`,`-n 1` → `C − A` = prefill 增量(`|P'| − |P|` 个 prompt token)。

所有 schedule 使用完全相同的 `P`、`P'`、`T`、seed、线程数,差分值才可跨 schedule 直接比较。
报告口径:`insns/decode-token = (B−A)/T`,按指标分类分别给出。

Tier 1 允许主张:动态指令数(总量/向量算术/访存)降低百分比;`vsetvl` 占比与开销比;
指令混合比(如 v_arith : v_load);结论与微架构无关(architecture-independent)。
Tier 1 不允许主张:任何涉及存储层次(cache/带宽/预取)、指令延迟、发射宽度的结论;
不得给出 tokens/s、加速比、TTFT 等任何时间量。QEMU 计时数据一律不进论文。

### Tier 2 — gem5 周期近似仿真(可选,仅作交叉验证)

必须标注 "cycle-approximate"。截至 2026-09,gem5 的 RVV timing model 未经实硬件校准验证,
其绝对周期数与排序均可能失真。仅用于:与 Tier 1 指令数趋势、Tier 3 实测趋势做一致性交叉检查。
gem5 数据不得作为任何性能主张的唯一证据。

### Tier 3 — 真实 RVV 硅片(黄金标准)

目标平台:Banana Pi BPI-F3 / SpacemiT K1(VLEN=256)、Milk-V Jupiter;记录 SoC、内核版本、内存配置。
指标:`tokens/s`(pp/tg,经 `llama-bench`)、TTFT/TPOT(经 `llama-batched-bench` 或计时封装)、
硬件性能计数器(`perf stat`:cycles、instructions、cache-misses、可用时的 stall 事件)。
复用 `vb-tools/sweep-schedules.sh` 的 CSV sweep 流程(去掉 qemu 前缀,`host` 列填板卡名)。
所有 tokens/s、加速比、延迟主张只能出自 Tier 3。

## 3. 重复与方差策略

- Tier 1(QEMU 指令计数):确定性,1 次即可;但每个 config 追加 1 次重复运行验证计数逐位一致,
  不一致则视为环境污染(如后台线程数漂移),整批作废排查。
- Tier 3(真机):每 config 至少 5 次重复(`llama-bench -r 5` 或脚本层循环),丢弃第 1 次 warmup,
  报告 mean ± std;若 std/mean > 3% 需加测并说明来源(热节流、governor)。
- Tier 2:与 Tier 3 相同重复策略(仿真非确定性来源:线程调度)。

## 4. 工作负载网格

- 主网格:pp ∈ {32, 128, 512} × tg ∈ {8, 32, 128}(`llama-bench -p ... -n ...`)。
- Tier 1 差分:`P` 取 pp=32 对应 prompt,`P'` 取 pp=128;`T ∈ {8, 32}`。
- 后续扩展:batch size 维度经 `llama-batched-bench`(留待 serving 场景实验,列于 CSV 同一模式)。
- 量化类型覆盖:q4_0 为主线;q8_0 / q2_K / q4_K / q5_K / iq4_nl / mxfp4 按同网格抽样(pp=128, tg=32)。

## 5. 基线表 (Baselines)

| 名称 | 定义 | 作用 |
|---|---|---|
| `norepack` | `-DGGML_CPU_REPACK=OFF` 构建,标量/通用路径 | 绝对下界基线 |
| `default` | repack 构建,不设 `GGML_RVV_SCHEDULE`,上游默认选择逻辑 | 对照上游 |
| `q4_0_8x1` … `q4_0_64x1`, `q4_0_8x8` 等 | `GGML_RVV_SCHEDULE=<name>` 强制单一 schedule | 搜索空间逐点 |
| `learned`(后续) | 学习得到的 dispatch 策略 | 论文主贡献对照 |

非法强制(如 vlen=256 下 `q4_0_64x1`)按设计回退到 un-repacked 路径,须在日志中确认回退并在结果中标注。
正确性前置:任何进入本协议的 config 必须先通过 `vb-tools/qemu-validate.sh`
(greedy `llama-simple` 输出跨 VLEN/schedule 与 norepack 参考逐字一致)。

## 6. 报告模板

统一 CSV 列(Tier 1/3 共用,不适用列填空):

```
tier,host,git_commit,vlen,schedule,quant,test,threads,
insns_total,v_arith,vsetvl,v_load,v_store,          # Tier 1 差分值 (per decode-token 或 per prefill-token)
t_per_s_mean,t_per_s_std,reps,                      # Tier 3
cycles,instructions,cache_misses                    # Tier 3 perf stat(可选)
```

论文正文规范表格(每张表注明 Tier、commit、环境串):

```markdown
| schedule | vlen | pp512 t/s (±std) | tg128 t/s (±std) | v_arith/tok | vsetvl/tok | Δ vs default |
|---|---|---|---|---|---|---|
```

## 7. 主张政策 (Claims Policy)

允许的句式(按数据来源层级):

- Tier 1:"schedule X 相比 default 将每 decode token 的动态向量算术指令减少 Y%。"
- Tier 1:"schedule X 的 `vsetvl` 指令占向量指令总数的 Y%,为 Z 的 W 倍。"
- Tier 1:"该指令数削减与具体微架构无关,由 ISA 级 schedule 结构决定。"
- Tier 2:"gem5(cycle-approximate,RVV timing 未校准)的周期趋势与 Tier 1/3 一致。"
- Tier 3:"在 SpacemiT K1(VLEN=256)上,schedule X 使 tg128 达到 Y tokens/s,较 default 提升 Z%(mean±std, n≥5)。"

禁止的句式:

- 由 QEMU 数据(Tier 1)得出:"在 RISC-V 硬件上获得 X 倍加速"、任何 tokens/s / 延迟 / 能效数字。
- 由 QEMU llama-bench 计时得出任何结论(该计时仅用于流水线冒烟,见 `sweep-schedules.sh` 头注)。
- 由 gem5 单独得出任何加速比或绝对性能数字。
- 由指令数减少直接推断时间加速("指令少 30% 所以快 30%")—— 两者仅能分别陈述,由 Tier 3 建立关联。
- 将单一板卡的 Tier 3 结果泛化为 "RISC-V 硬件普遍如此",除非至少两个不同微架构复现。
