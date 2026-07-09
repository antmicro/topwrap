# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.misc import Identifier


class TestIdentifierCombined:
    def test_combined_ignores_version_by_design(self):
        # combined() intentionally excludes version; it's a version-less type key.
        v1 = Identifier(name="AXI4", vendor="amba.com", library="AMBA4", version="1.0")
        v2 = Identifier(name="AXI4", vendor="amba.com", library="AMBA4", version="2.0")

        assert v1 != v2
        assert v1.combined() == v2.combined()
