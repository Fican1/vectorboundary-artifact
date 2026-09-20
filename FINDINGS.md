# VectorBoundary — 论文级发现汇总

> 生成: 2026-09-16。本文档只收录**机制/实证发现**（能直接写进 Motivation/Results 章节的东西），
> 不重复文献定位材料（那些在 BASELINES.md / DAC-COMPARABLES.md / BENCHMARK-ALIGNMENT.md）。
> 每条发现标注：证据来源文件、可信度、对论文的用途。

---

## 发现 1：真实上游 correctness bug（legality mask 存在的直接理由）

**是什么**：q4_0 8x8 RVV kernel（`ggml/src/ggml-cpu/arch/riscv/repack.cpp`）的 `vlenb >= QK4_0` 分支假设 128 字节寄存器组（vlenb=32 时的 LMUL=4 布局），在 vlenb=64/128（VLEN=512/1024）上产生**完全错误的数值输出**（QEMU 复现为乱码 token）。这条路径在非 zvfh 构建的宽 VLEN 机器上是**默认路径**，不是边角案例。

**证据**：QEMU 强制 `q4_0_8x8` 在 vlen=512 生成乱码；修复（精确匹配 `== QK4_0` + registry 加 `max_vlenb=32`）后 11/11 场景与标量参考逐 token 一致。commit `449f9bde4`。

**可信度**：✅ 确定（编译验证 + QEMU 复现 + 修复后回归通过）。

**论文用途**：legality mask 不是形式设计的最强证据——手工 if/else 链把这个组合"隐藏"起来，registry 把它暴露出来，暴露的第一件事就是 bug。可考虑正式提交给上游（需用户本人操作）。

---

## 发现 2：指令数排名 ≠ 真实/仿真墙钟排名（两次反转，方向相反）

**是什么**：
- VLEN=256 decode：指令数最少的是 8x8（49.9M），但 QEMU 墙钟里 **16x1 反而快 35%**。
- VLEN=1024：指令数最少的是 64x1（19.0M，符合"越宽越省指令"直觉），但墙钟里 **32x1 快 40%**。

**机制解释**：8x8 用更高的 vsetvl 开销换更少的算术指令（vlen=256 decode 下 8x8 的 vsetvl 占比 22%，16x1 只有 8%）；64x1 在实际执行中吃了额外的寄存器压力/尾效应，未体现在静态指令计数里。

**证据**：`insn-tables.md` + `sweep-qemu-full.csv`。

**可信度**：✅ 确定（同一构建、同一模型，两套独立测量互相印证）。

**论文用途**：核心方法论论据——**任何单一静态/指令级指标都无法唯一预测真实排名**，这是"为什么需要多特征校准 ranking 而不是贪心规则"的直接支撑。

---

## 发现 3：上游 VLEN 匹配规则的 oracle-gap（量化了"现有方案有多差"）

**是什么**：上游默认选择规则（按 VLEN 宽度机械匹配 Nx1 kernel）在扩展后的 23 个真实上下文中，相对 oracle（每上下文最优 schedule）：
- 均值命中 oracle 的 **84.0%**，最差上下文只有 **43.0%**。
- 命中率（恰好选中最优）仅 **39%**（9/23）。
- **更正（2026-09-16）**：早期算出的"2.08×"是数据缺失导致的误判——q8_0_16x1 那组当时因超时缺了数据，脚本误把 q8_0_8x1（796M，确实差 2.1×）当成了上游规则实际选择的 kernel。补全数据后核实：VLEN=256 下上游规则对 Q8_0 实际选的是 **q8_0_16x1**（402.7M），真实 oracle 是 **norepack 本身**（383.3M）——上游只比不打包差 **5%**（score=0.952），不是 2.1×。
- 跨模型汇总（vlen=256，7 个 model×quant 组合 × decode/prefill，共 14 个上下文）：上游规则均值命中 oracle 的 **85.1%**，最差 **59.6%**（SmolLM2-135M Q4_0 prefill：选了 16x1 而 8x8 是 oracle），精确命中率 **29%**（4/14）。
- 仍然值得记录的真实发现：**Qwen3-0.6B Q8_0 decode 是唯一一个"真实 oracle 是完全不打包"的上下文**——这里所有 repack schedule（8x1、16x1）都比 legacy vec_dot 路径差，量化格式和模型规模的组合使打包本身变成负收益，不只是"选错了哪个 schedule"的问题。

**证据**：`eval-ranking.py` 输出 + `dataset.csv`。

**可信度**：✅ 确定（真实测量，非合成）。**重要交叉验证**：6 月的合成分析（自建 F0 proxy）已经预言"Decode + Q8 宽配置容易出现 wide-worse-than-narrow"——现在用真实指令计数在完全不同的模型（Qwen3-0.6B vs 当时的合成 workload）上复现了同一个失败模式。这是 methodology 从 proxy 过渡到真实测量后**方向一致性**的证明。

**论文用途**：主结果之一。且提供了一个具体的 failure case study（Qwen3-0.6B Q8_0 decode），可作为审稿人最容易信服的例子。

---

## 发现 4：Batch 边界是台阶函数，不是斜坡，位置与代码逐字对应

**是什么**：每 decode token 的指令数（vlen=256）随 batch 变化：
- batch 1→2：几乎不变。
- **batch 3→4：所有 repack schedule 突降 17–34%**（8x1: −20%, 16x1: −17%, 8x8: −34%）；batch 4 和 8 完全相同数值。
- norepack（legacy vec_dot 路径）四个 batch 完全不变（116.1M→114.2M，噪声级差异）。

**机制**：`repack.cpp` 的 `forward_mul_mat` 里硬编码 `nrows > 3` 触发 GEMV→GEMM 切换（4 行一组处理）；权重加载指令在跨过边界后从 9.09M/token 崩到 2.57M/token（−72%，8x1 案例）——GEMM 按行摊销权重读取。

**证据**：`batch-curve.md`。

**可信度**：✅ 确定（机制→代码位置→测量三者吻合）。

**论文用途**：这是"vectorization-profitability boundary"在真实代码里的**第一手实测证据**，不是假设。可以直接画成论文的标志性图（x 轴 batch，y 轴 insn/token，四条线在 batch=4 处一起拐弯）。同时说明：1-bit 的 stage（prefill/decode）dispatch（如 VectorWeaver）不够，因为同一个 stage 内部也存在边界。

---

## 发现 5：Decode 内存流量是 compulsory 的，与 schedule 和 cache 容量都无关

**是什么**：对照两组 cache 配置（L1D 32K+L2 512K vs L1D 128K+L2 2M，容量差 4 倍）× 3 个 schedule：
- 每 decode token 的 L1D 缺失几乎不变（~1.50–1.53M/token，跨 schedule、跨容量差异 <2%）。
- L2 缺失 ≈ L1D 缺失（几乎每次 L1D miss 都穿透到 L2/内存）。
- 92MB 权重 ÷ 64B cache line ≈ 1.44M 行，与实测缺失数量级吻合。

**证据**：`cache-qemu.csv`。

**可信度**：✅ 确定（两组独立容量配置交叉验证，且数值与理论计算吻合）。

**论文用途**：decode 侧 boundary 的**物理机制**解释——schedule 只能优化指令侧（已测 2–6×），内存侧是常数、任何 schedule 都消不掉，唯一杠杆是量化格式本身。这把"为什么 decode 收益天花板低"从直觉变成可计算的数字。

---

## 发现 6：Shape 轴上也存在边界（kernel 级方阵扫描，对齐 Peccia ICCAD'25）

**是什么**：8x8 相对 16x1 的指令数优势随矩阵规模增大而**单调收缩**：32×32 时 5.6×，64×64 时 4.8×，128×128 时 3.4×，256×256 时 2.5×，512×512 时 2.0×。M=1（decode-like）列的优势收缩更快。

**证据**：`shapes-qemu.csv`（`vb-shape-bench` 工具产出，80 组数据点）。

**可信度**：✅ 确定。

**论文用途**：boundary 现象的第三个独立轴（此前是 VLEN 轴、batch 轴），证明这不是单一维度的现象，而是 shape × batch × VLEN × quant 的联合边界——支撑"需要多维特征而不是单查表"的方法论选择。

---

## 发现 7：Selection 方法的量化增量（核心方法结果）

**是什么**：13 特征白盒 ridge 回归，leave-one-context-out 交叉验证（23 个真实上下文，跨 6 个模型×量化组合、4 个 VLEN、4 个 batch）：

| 策略 | 均值 oracle-score | 最差 | top-1 命中率 |
|---|---:|---:|---:|
| 我们（top-1） | 0.970 | 0.481 | 87% |
| 我们（top-2） | **1.000** | 0.993 | **96%** |
| 上游 VLEN 规则 | 0.840 | 0.430 | 39% |
| 最宽合法启发式 | 0.810 | 0.430 | 30% |
| 随机 | 0.683 | 0.512 | 0% |

**对齐外部指标**：Rtop1（Pelke, DAC'25 风格）95%（早期 19 context 版本，待用 23-context 重算）；同轴对比 VectorWeaver 的跨芯片 75% ranking accuracy、TLP 的 top-1 0.87–0.92。

**证据**：`eval-ranking.py` 输出（今日已用完整 23-context 数据集重跑）。

**可信度**：✅ 方法有效但**样本量偏小**（23 context，需要在扩数据集后复核跨模型泛化的稳健性；Qwen3-0.6B Q8_0 decode 是目前最差的失败案例，top-1 未命中但 top-2 命中）。

**论文用途**：这是论文的核心方法学结果——证明"学习式 selection"比"厂商启发式规则"有实质增量，且是跨模型/量化/VLEN/batch 的留出验证，不是同分布过拟合。

---

## 发现 8：PPL 数值不变性（正确性保真的独立证明）

**是什么**：SmolLM2-135M Q4_0 在 WikiText-2 上，default schedule 与强制 `q4_0_8x8`（合法配置下）产生**逐位相同**的困惑度：21.8390 ± 1.41650。

**证据**：`ppl-default.log` / `ppl-force8x8.log`。

**可信度**：✅ 确定。norepack 基线的同项验证仍在跑（预计很快完成）。

**论文用途**：证明"schedule 选择只影响性能、不影响数值正确性"（对合法 schedule 而言）——呼应 VectorWeaver 用 PPL 验证保真的惯例，同时与发现 1 的 bug 形成对比（非法/越界 schedule 才会破坏正确性）。

---

## 发现 9：Legacy（非 repack）路径完全不随 VLEN 扩展

**是什么**：`norepack`（上游未启用 repack 的通用 `vec_dot` 路径）在 VLEN=128/256/512/1024 下每 token 指令数几乎不变（116.4M → 115.4M，噪声级差异），而所有 repack schedule 都随 VLEN 单调下降。

**证据**：`insn-tables.md`。

**可信度**：✅ 确定。

**论文用途**：说明"向量宽度的收益必须由显式 tiling/repack 结构才能兑现"，静态 vec_dot 循环对更宽机器视而不见——这是 motivation 部分很直观的一张图（一条平线 vs 四条下降线）。

---

## 发现 10：部署模型在真实模型矩阵形状上的外推鲁棒性检查

**背景**：训练/验证用的 shape 网格只有 32-512（5 档，均匀对数间隔），40 个留出样本 100% 命中 oracle。这个数字容易让人怀疑"网格太规整太小，是不是在玄插值玩具数据"。

**验证方法**：直接取四个真实 benchmark 模型（SmolLM2-135M/360M, Qwen2.5-0.5B, Qwen3-0.6B）的真实 hidden/FFN 矩阵形状（576/1536/960/2560/896/4864/1024/3072，**全部超出训练网格上限 512**），用部署到 C++ 里那套权重原样打分，对照 QEMU 实测的真实 oracle。

**结果**：32/32（8 个真实形状 × 2 个 VLEN × 2 个 batch 画像）全部命中。

**必须说清的限定**：这次真实形状检查里，oracle 在同一 VLEN 下对所有 8 个形状**从未换过人**（VLEN=256 全是 8x8，VLEN=1024 全是 64x1）——大尺寸下 boundary 已经"拉平"，不同形状不再需要模型去区分谁更优。所以这个检查证明的是"外推不会突然失效变成瞎选"，而不是"细粒度排序能力"——那个能力由 32-512 网格上的留出验证证明（那里不同形状之间 oracle 确实换过人）。两个证据强度不同，论文（main.tex RQ2）已经分开陈述，不合并成同一个"100%"重复宣称。

**证据**：`vb-tools/realshapes-v256.csv`、`vb-tools/realshapes-v1024.csv`、`vb-tools/sweep-realshapes.sh`。

**可信度**：✅ 确定（直接复用部署权重，非重新拟合）。

---

## 待验证 / 进行中

- norepack 的 PPL 复验（预计今日完成，补齐发现 8 的完整对照组）
- Rtop1/Etop1 在完整 23-context 数据集上的重算（当前 95% 是 19-context 早期版本）
- Runtime dispatch 的端到端收益（尚未实现，是发现 7 从"排序质量"落到"真实端到端提升"的最后一环）
- 真机（BPI-F3）时序验证——所有以上发现目前都在**QEMU 指令数/仿真 cache**轴上；时序轴的排名是否与指令轴一致或背离，本身就是可写的 RQ

---

## 原始数据索引

| 发现 | 数据文件 |
|---|---|
| 1 | commit `449f9bde4`；`qemu-validate.sh` 输出 |
| 2 | `insn-tables.md`, `sweep-qemu-full.csv` |
| 3 | `dataset.csv`, `eval-ranking.py` |
| 4 | `batch-curve.md`, `batch-qemu.csv` |
| 5 | `cache-qemu.csv` |
| 6 | `shapes-qemu.csv` |
| 7 | `dataset.csv`, `eval-ranking.py` |
| 8 | `ppl-*.log` |
| 9 | `insn-tables.md` |
