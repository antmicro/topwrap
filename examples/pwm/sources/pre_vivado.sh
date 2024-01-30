# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
echo "Prebuild script started."
sed -i 's/launch_runs synth_1/launch_runs synth_1 -jobs 16/g' project_1_0_synth.tcl
sed -i 's/source_mgmt_mode None/source_mgmt_mode All/g' project_1_0.tcl
echo "Prebuild done."
