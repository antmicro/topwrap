from topwrap.model.misc import Identifier

from .advanced.ir.design import module as adv_top
from .advanced.ir.design import proc_mod, seq_sci_mod, sseq_mod
from .clocks.ir.design import axis_cdc, axis_clk_receiver, axis_clk_streamer
from .clocks.ir.design import module as clk_top
from .hierarchical.ir.design import adder, bitcnt4, d_ff, debouncer, encoder, proc
from .hierarchical.ir.design import top as hier_top
from .interconnect.ir.design import cpu, dsp, mem
from .interconnect.ir.design import top as intr_top
from .interface.ir.design import axis_receiver, axis_streamer
from .interface.ir.design import module as intf_top
from .inverted.ir.design import inv_adder, inv_crg
from .inverted.ir.design import module as inv_top
from .simple.ir.design import lfsr_gen, two_mux
from .simple.ir.design import module as simp_top

hier_top.id = Identifier("hier_top")
intr_top.id = Identifier("intr_top")
intf_top.id = Identifier("intf_top")
simp_top.id = Identifier("simp_top")
clk_top.id = Identifier("clk_top")

ALL_MODULES = [
    adder,
    axis_cdc,
    axis_clk_streamer,
    axis_clk_receiver,
    clk_top,
    d_ff,
    debouncer,
    encoder,
    bitcnt4,
    proc,
    hier_top,
    cpu,
    dsp,
    mem,
    intr_top,
    axis_streamer,
    axis_receiver,
    intf_top,
    lfsr_gen,
    two_mux,
    simp_top,
    sseq_mod,
    seq_sci_mod,
    proc_mod,
    adv_top,
    inv_crg,
    inv_adder,
    inv_top,
]
