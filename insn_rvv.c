/*
 * VectorBoundary: QEMU TCG plugin counting dynamic RISC-V instruction mix.
 * Reports total instructions, OP-V arithmetic, vsetvl family, vector
 * loads/stores. Counts are exact per-execution via inline counters.
 *
 * build: gcc -shared -fPIC -I<qemu-include> insn_rvv.c -o libinsn_rvv.so
 * usage: qemu-riscv64 -plugin ./libinsn_rvv.so -d plugin -D counts.txt ...
 */
#include <inttypes.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include <qemu-plugin.h>

QEMU_PLUGIN_EXPORT int qemu_plugin_version = QEMU_PLUGIN_VERSION;

enum {
    CLS_TOTAL = 0,
    CLS_VARITH,
    CLS_VSETVL,
    CLS_VLOAD,
    CLS_VSTORE,
    CLS_N
};

static const char * cls_names[CLS_N] = {
    "insns_total", "v_arith", "vsetvl", "v_load", "v_store"
};

static struct qemu_plugin_scoreboard * sbs[CLS_N];
static qemu_plugin_u64 counts[CLS_N];

static int classify(uint32_t insn) {
    if ((insn & 0x3) != 0x3) {
        return -1; /* compressed, never vector */
    }
    uint32_t opc = insn & 0x7f;
    if (opc == 0x57) {
        return ((insn >> 12) & 0x7) == 0x7 ? CLS_VSETVL : CLS_VARITH;
    }
    if (opc == 0x07 || opc == 0x27) {
        /* LOAD-FP/STORE-FP width 0,5,6,7 = vector element widths 8/16/32/64 */
        uint32_t width = (insn >> 12) & 0x7;
        if (width == 0x0 || width >= 0x5) {
            return opc == 0x07 ? CLS_VLOAD : CLS_VSTORE;
        }
    }
    return -1;
}

static void vcpu_tb_trans(qemu_plugin_id_t id, struct qemu_plugin_tb * tb) {
    size_t n = qemu_plugin_tb_n_insns(tb);
    for (size_t i = 0; i < n; i++) {
        struct qemu_plugin_insn * insn = qemu_plugin_tb_get_insn(tb, i);
        uint32_t data = 0;
        qemu_plugin_insn_data(insn, &data, sizeof(data));
        qemu_plugin_register_vcpu_insn_exec_inline_per_vcpu(
            insn, QEMU_PLUGIN_INLINE_ADD_U64, counts[CLS_TOTAL], 1);
        int c = classify(data);
        if (c >= 0) {
            qemu_plugin_register_vcpu_insn_exec_inline_per_vcpu(
                insn, QEMU_PLUGIN_INLINE_ADD_U64, counts[c], 1);
        }
    }
}

static void plugin_exit(qemu_plugin_id_t id, void * p) {
    char buf[128];
    for (int i = 0; i < CLS_N; i++) {
        snprintf(buf, sizeof(buf), "%s: %" PRIu64 "\n",
                 cls_names[i], qemu_plugin_u64_sum(counts[i]));
        qemu_plugin_outs(buf);
    }
}

QEMU_PLUGIN_EXPORT int qemu_plugin_install(qemu_plugin_id_t id,
                                           const qemu_info_t * info,
                                           int argc, char ** argv) {
    for (int i = 0; i < CLS_N; i++) {
        sbs[i] = qemu_plugin_scoreboard_new(sizeof(uint64_t));
        counts[i] = qemu_plugin_scoreboard_u64(sbs[i]);
    }
    qemu_plugin_register_vcpu_tb_trans_cb(id, vcpu_tb_trans);
    qemu_plugin_register_atexit_cb(id, plugin_exit, NULL);
    return 0;
}
