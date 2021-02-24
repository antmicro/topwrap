# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from nmigen import Fragment
from nmigen.back import verilog


class TestIPConnect:
    def test_generator(self):
        '''
        This test creates wrappers for 2 IPs
        and connects them in a separate module
        '''
        from fpga_topwrap.ipwrapper import IPWrapper
        from fpga_topwrap.ipconnect import IPConnect
        # wrap IPs
        dma = IPWrapper(yamlfile='tests/data/DMATop.yaml', ip_name='DMATop')
        disp = IPWrapper(yamlfile='tests/data/axi_dispctrl_v1_0.yaml',
                         ip_name='axi_dispctrl_v1_0')

        dma_fragment = Fragment.get(dma, None)
        disp_fragment = Fragment.get(disp, None)
        assert verilog.convert(dma_fragment,
                               name=dma.top_name, ports=dma.get_ports())
        assert verilog.convert(disp_fragment,
                               name=disp.top_name, ports=disp.get_ports())

        # connect the IPs in another module
        connector = IPConnect()
        connector.add_ip(dma)
        connector.add_ip(disp)
        connector.connect_interfaces('AXIS_m0', dma.top_name,
                                     'AXIS_s0', disp.top_name)
        # connect output of disp to two inputs of dma
        connector.connect_ports('io_sync_writerSync', dma.top_name,
                                'HSYNC_O', disp.top_name)
        connector.connect_ports('io_sync_readerSync', dma.top_name,
                                'HSYNC_O', disp.top_name)

        fragment = Fragment.get(connector, None)
        assert verilog.convert(fragment, name='top')
