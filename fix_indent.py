import sys

with open("data_capture/management/commands/capture_demand_data.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # lines 93 to 308 are 1-indexed (so index 92 to 307)
    if 92 <= i <= 307:
        if line.strip() != "":
            new_lines.append("    " + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open("data_capture/management/commands/capture_demand_data.py", "w") as f:
    f.writelines(new_lines)

print("Indentation fixed.")
