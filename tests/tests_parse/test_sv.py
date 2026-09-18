import logging
from pathlib import Path

import pytest

from topwrap.frontend.frontend import FrontendParseException
from topwrap.frontend.sv.frontend import SystemVerilogFrontend

SV_MODULE = """
module simple_module(
    input logic clk,
    output logic data
);
endmodule
"""


class TestSystemVerilogFrontend:
    def test_parse_valid_module(self):
        parsed = SystemVerilogFrontend().parse_str([SV_MODULE])

        [module] = parsed.modules
        assert module.id.name == "simple_module"
        assert [port.name for port in module.ports] == ["clk", "data"]

    def test_parse_files(self, tmp_path: Path):
        source = tmp_path / "simple_module.sv"
        source.write_text(SV_MODULE)

        parsed = SystemVerilogFrontend().parse_files([source])

        [module] = parsed.modules
        assert module.id.name == "simple_module"

    def test_syntax_errors_are_reported_as_errors(self, caplog: pytest.LogCaptureFixture):
        invalid_source = """
        module broken_module(
            this is not a valid port declaration;
        );
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FrontendParseException, match="expected"):
                SystemVerilogFrontend().parse_str([invalid_source])

    def test_missing_module_is_reported_as_warning(self, caplog: pytest.LogCaptureFixture):
        incomplete_source = """
        module top(input logic clk);
            missing_module u_missing(.clk(clk));
        endmodule
        """

        with caplog.at_level(logging.WARNING):
            parsed = SystemVerilogFrontend().parse_str([incomplete_source])

        [module] = parsed.modules
        assert module.id.name == "top"
        assert "unknown module 'missing_module'" in caplog.text
        assert any(record.levelno == logging.WARNING for record in caplog.records)
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_multiple_semantic_diagnostics_are_reported_in_multiple_warnings(
        self, caplog: pytest.LogCaptureFixture
    ):
        incomplete_source = """
        module top;
            unknown_a a();
            unknown_b b();
        endmodule
        """

        with caplog.at_level(logging.WARNING):
            SystemVerilogFrontend().parse_str([incomplete_source])

        warning_records = [
            record
            for record in caplog.records
            if record.name == "topwrap.frontend.sv.frontend" and record.levelno == logging.WARNING
        ]
        assert len(warning_records) == 2
        assert "unknown module 'unknown_a'" in warning_records[0].message
        assert "unknown module 'unknown_b'" in warning_records[1].message

    def test_unknown_macro_in_module_body_is_ignored(self, caplog: pytest.LogCaptureFixture):
        source = """
        module top;
            `UNKNOWN_MACRO(argument)
        endmodule
        """

        with caplog.at_level(logging.WARNING):
            parsed = SystemVerilogFrontend().parse_str([source])

        assert [module.id.name for module in parsed.modules] == ["top"]
        assert "UNKNOWN_MACRO" not in caplog.text

    def test_unknown_macro_in_module_header_is_an_error(self):
        source = """
        module top(
            `UNKNOWN_MACRO(argument)
        );
        endmodule
        """

        with pytest.raises(FrontendParseException, match="unknown macro"):
            SystemVerilogFrontend().parse_str([source])

    def test_missing_include_is_reported_as_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ):
        source = tmp_path / "missing_include.sv"
        source.write_text('`include "does_not_exist.svh"\nmodule top; endmodule\n')

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FrontendParseException):
                SystemVerilogFrontend().parse_files([source])

    def test_parse_multiple_sources(self):
        parsed = SystemVerilogFrontend().parse_str(
            [
                "module first; endmodule",
                "module second; endmodule",
            ]
        )

        assert {module.id.name for module in parsed.modules} == {"first", "second"}

    def test_parse_interface(self):
        source = """
        interface simple_if;
            logic data;
        endinterface
        """

        parsed = SystemVerilogFrontend().parse_str([source])

        assert [interface.id.name for interface in parsed.interfaces] == ["simple_if"]
