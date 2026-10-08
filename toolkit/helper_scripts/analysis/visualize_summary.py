"""Build a consistently sized, automatically sized analysis report.

Run from any directory; inputs and the PDF live beside this script.
Tables continue onto another page; device charts grow taller to fit every record.
"""
import os
import json
import re
import math
from pathlib import Path
from packaging.version import Version

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

PAGE_SIZE = (14, 8.5)
PAGE_WIDTH, PAGE_HEIGHT = (value * 72 for value in PAGE_SIZE)
MAX_COMMIT_HISTORY = 60
INK = "#E6EDF7"
MUTED = "#A5B4C9"
PAPER = "#0E1624"
SURFACE = "#162234"
SURFACE_ALT = "#1C2B40"
TABLE_HEADER = "#2A3C55"
BORDER = "#304158"
TEAL = "#58D5C9"
BLUE = "#91A7FF"
AMBER = "#F2BD65"
COLORS = [TEAL, BLUE, "#C4A0ED", "#F29D7D", "#A9CD85", "#E69BBB"]
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 10,
    "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": BORDER, "axes.facecolor": SURFACE,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.axisbelow": True, "grid.color": BORDER,
    "grid.linewidth": 0.6, "lines.linewidth": 1.8,
    "legend.frameon": False, "pdf.fonttype": 42,
    "text.usetex": False, "text.parse_math": False,
    "savefig.bbox": None,
}


def _page(title, subtitle, section):
    fig = plt.figure(figsize=PAGE_SIZE, facecolor=PAPER)
    fig.text(0.045, 0.946, "micrOS  /  ENGINEERING REPORT", fontsize=9,
             weight="bold", color=TEAL)
    fig.text(0.955, 0.946, section.upper(), fontsize=9, color=MUTED, ha="right")
    fig.text(0.045, 0.883, title, fontsize=24, weight="bold")
    fig.text(0.045, 0.844, subtitle, fontsize=10, color=MUTED)
    fig.add_artist(plt.Line2D([0.045, 0.955], [0.075, 0.075],
                             transform=fig.transFigure, color=BORDER, lw=0.8))
    return fig


def _save(pdf, fig, note="micrOS / DevToolKit"):
    fig.text(0.045, 0.041, note, fontsize=8, color=MUTED)
    fig.text(0.955, 0.041, f"{pdf.get_pagecount() + 1:02d}",
             fontsize=9, color=MUTED, ha="right")
    pdf.savefig(fig, facecolor=PAPER)
    plt.close(fig)


def _card(fig, bounds):
    fig.add_artist(FancyBboxPatch(
        bounds[:2], bounds[2], bounds[3], transform=fig.transFigure,
        boxstyle="round,pad=0,rounding_size=0.012", facecolor=SURFACE,
        edgecolor=BORDER, linewidth=0.6, zorder=-1))


def page_report_intro(pdf, versions, has_device_metrics):
    fig = _page("micrOS platform analytics", "A guide to platform evolution, dependencies and engineering health", "Overview")
    fig.text(0.045, 0.785,
             f"{versions[0]} to {versions[-1]}  /  {len(versions)} recorded versions",
             fontsize=12, weight="bold", color=TEAL)
    fig.text(0.045, 0.745,
             "Explore how the runtime grows, which files it depends on, and how the project performs.",
             fontsize=11, color=MUTED)
    categories = [
        ("Evolution", "Core, load module and package growth across versions.\nCompare file counts and source lines over time."),
        ("Dependencies", "Core reference histories, ranked by latest count.\nLower-reference files are listed separately."),
        ("People", "Contribution shares and contributor areas.\nSee who contributes and which files they work on."),
        ("Quality", "Pylint scores and load module dependency warnings.\nTrack code quality and dependency checks over time."),
    ]
    if has_device_metrics:
        categories.append(("Devices", "Recorded device benchmarks and module inventories.\nCompare measured performance and loaded modules."))
    categories.append(("History", "Recent version commits, with newest entries first.\nRead the full commit messages at the end of the report."))
    for i, (title, description) in enumerate(categories):
        x, y = 0.045 + (i % 2) * 0.465, 0.535 - (i // 2) * 0.205
        _card(fig, (x, y, 0.445, 0.18))
        fig.text(x + 0.018, y + 0.132, title, fontsize=14, weight="bold", color=TEAL)
        fig.text(x + 0.018, y + 0.085, description, fontsize=10, color=MUTED,
                 va="top", linespacing=1.6)
    _save(pdf, fig, "Reading order: left to right, top to bottom. Sections continue across pages as needed.")


def _timeline_axis(ax, versions, highlighted_versions=(), max_labels=14):
    # Thin labels only: every recorded value remains in the plotted series.
    step = max(1, math.ceil((len(versions) - 1) / (max_labels - 1)))
    ticks = list(range(0, len(versions), step))
    if len(versions) > 1 and ticks[-1] != len(versions) - 1:
        if len(versions) - 1 - ticks[-1] < step * 0.65:
            ticks.pop()
        ticks.append(len(versions) - 1)
    ax.set_xticks(ticks, [versions[i] for i in ticks], rotation=35, ha="right")
    ax.set_xlim(-0.5, max(0.5, len(versions) - 0.5))
    ax.grid(axis="y")
    ax.tick_params(axis="both", length=0, pad=7)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.margins(y=0.18)
    for index, version in enumerate(versions):
        if version in highlighted_versions:
            ax.axvline(index, color=AMBER, alpha=0.25, lw=0.9, linestyle="--")


def _series(ax, values, color):
    ax.plot(range(len(values)), values, color=color, marker="o", markersize=3,
            markeredgecolor=SURFACE, markeredgewidth=0.35)
    ax.scatter([len(values) - 1], [values[-1]], s=28, color=color, zorder=4)


def _evolution(pdf, versions, first, second, releases, title, first_label):
    fig = _page(title, f"{versions[0]} to {versions[-1]}  /  {len(versions)} recorded versions", "Evolution")
    for top, values, label, color in [(0.78, first, first_label, TEAL),
                                       (0.44, second, "Lines of code", BLUE)]:
        _card(fig, (0.045, top - 0.31, 0.91, 0.31))
        fig.text(0.065, top - 0.038, label, fontsize=11, weight="bold")
        fig.text(0.935, top - 0.04, f"{values[-1]:,} latest", fontsize=14,
                 weight="bold", color=color, ha="right")
        ax = fig.add_axes([0.10, top - 0.225, 0.82, 0.16])
        _series(ax, values, color)
        _timeline_axis(ax, versions, releases)
    _save(pdf, fig, "All recorded values shown. Version labels spaced for readability. Dashed amber lines: official releases.")


def page_core_system(pdf, versions, core_files, highlighted_versions, core_lines):
    _evolution(pdf, versions, core_files, core_lines, highlighted_versions,
               "Core system evolution", "Core files")


def page_load_modules(pdf, versions, load_files, highlighted_versions, load_lines):
    _evolution(pdf, versions, load_files, load_lines, highlighted_versions,
               "Load module evolution", "Load modules")


def page_packages(pdf, versions, package_counts, highlighted_versions, package_lines):
    _evolution(pdf, versions, package_counts, package_lines, highlighted_versions,
               "Package evolution", "Packages")


def _wrap_text(fig, text, width_points, size=10, family="DejaVu Sans"):
    """Wrap against actual font widths, including unbroken hashes and paths."""
    renderer = fig.canvas.get_renderer()
    font = FontProperties(family=family, size=size)
    width_pixels = width_points * fig.dpi / 72
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        # Wrapping words first keeps prose readable; a long token can still split.
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            if renderer.get_text_width_height_descent(candidate, font, False)[0] <= width_pixels:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ""
            for char in word:
                if line and renderer.get_text_width_height_descent(line + char, font, False)[0] > width_pixels:
                    lines.append(line)
                    line = ""
                line += char
        lines.append(line)
    return lines


def _table_pages(pdf, title, subtitle, headers, rows, widths, section):
    """Paginate by measured wrapped line height, never by shrinking the font."""
    if not rows:
        return
    fig = None
    cursor = 0
    left, table_width = 0.045 * PAGE_WIDTH, 0.91 * PAGE_WIDTH
    line_height, padding = 13, 6
    bottom = 0.105 * PAGE_HEIGHT
    for row_index, row in enumerate(rows):
        if fig is None:
            fig = _page(title, subtitle, section)
        cells = [_wrap_text(fig, value, table_width * width - 2 * padding)
                 for value, width in zip(row, widths)]
        while any(cells):
            if cursor == 0:
                cursor = 0.79 * PAGE_HEIGHT
                x = left
                for label, width in zip(headers, widths):
                    fig.add_artist(Rectangle((x / PAGE_WIDTH, (cursor - 27) / PAGE_HEIGHT),
                                             table_width * width / PAGE_WIDTH, 27 / PAGE_HEIGHT,
                                             transform=fig.transFigure, facecolor=TABLE_HEADER, edgecolor="none"))
                    fig.text((x + padding) / PAGE_WIDTH, (cursor - 8) / PAGE_HEIGHT,
                             label, color=INK, fontsize=9, weight="bold", va="top")
                    x += table_width * width
                cursor -= 27
            available_lines = int((cursor - bottom - 2 * padding) / line_height)
            needed_lines = max(map(len, cells))
            # Keep a row together if it will fit on a fresh page.
            fresh_capacity = int((0.79 * PAGE_HEIGHT - 27 - bottom - 2 * padding) / line_height)
            if available_lines < 1 or (needed_lines > available_lines and needed_lines <= fresh_capacity):
                _save(pdf, fig)
                fig = _page(title, subtitle + "  /  continued", section)
                cursor = 0
                continue
            take = min(needed_lines, available_lines)
            height = take * line_height + 2 * padding
            x = left
            for i, width in enumerate(widths):
                fig.add_artist(Rectangle((x / PAGE_WIDTH, (cursor - height) / PAGE_HEIGHT),
                                         table_width * width / PAGE_WIDTH, height / PAGE_HEIGHT,
                                         transform=fig.transFigure,
                                         facecolor=SURFACE if row_index % 2 == 0 else SURFACE_ALT, edgecolor="none"))
                fig.text((x + padding) / PAGE_WIDTH, (cursor - padding) / PAGE_HEIGHT,
                         "\n".join(cells[i][:take]), fontsize=10, va="top", linespacing=1.3)
                cells[i] = cells[i][take:]
                x += table_width * width
            cursor -= height
    if fig is not None:
        _save(pdf, fig)


def page_core_system_refs(pdf, core_refs_by_file, versions):
    ordered = sorted(core_refs_by_file.items(), key=lambda item: (-item[1][-1], item[0]))
    included = [(name, values) for name, values in ordered if values[-1] > 3]
    excluded = [(name, values[-1]) for name, values in ordered if values[-1] <= 3]
    for start in range(0, len(included), 4):
        fig = _page("Core references", "Per-file histories / latest reference count above 3", "Dependencies")
        for i, (name, values) in enumerate(included[start:start + 4]):
            x, y = 0.045 + (i % 2) * 0.465, 0.465 - (i // 2) * 0.34
            _card(fig, (x, y, 0.445, 0.315))
            fig.text(x + 0.018, y + 0.275, name, fontsize=11, weight="bold")
            fig.text(x + 0.425, y + 0.275, str(values[-1]), fontsize=13,
                     color=TEAL, weight="bold", ha="right")
            ax = fig.add_axes([x + 0.047, y + 0.095, 0.378, 0.15])
            _series(ax, values, TEAL)
            _timeline_axis(ax, versions, max_labels=6)
        _save(pdf, fig, "All recorded values shown. Each file uses its own vertical scale.")
    _table_pages(pdf, "Lower-reference core files", "Latest count of 3 or fewer / excluded from the trend charts",
                 ["File", "Latest references"], excluded, [0.78, 0.22], "Dependencies")


def page_pylint_scores(pdf, versions, core_scores, load_scores, highlighted_versions):
    fig = _page("Code quality", "Pylint scores across every recorded version", "Quality")
    _card(fig, (0.045, 0.13, 0.91, 0.65))
    ax = fig.add_axes([0.10, 0.245, 0.82, 0.415])
    for values, label, color in [(core_scores, "Core", TEAL), (load_scores, "Load modules", BLUE)]:
        _series(ax, values, color)
        ax.lines[-1].set_label(f"{label} / latest {values[-1]:.2f}")
    _timeline_axis(ax, versions, highlighted_versions)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.08), ncol=2, borderaxespad=0)
    _save(pdf, fig, "All recorded values shown. Dashed amber lines: official releases.")


def page_dep_warnings(pdf, versions, dependency_warnings):
    fig = _page("Dependency warnings", "Load module dependency checks across every recorded version", "Quality")
    _card(fig, (0.045, 0.13, 0.91, 0.65))
    fig.text(0.07, 0.717, f"{dependency_warnings[-1]:,} latest warnings", fontsize=15, color=AMBER, weight="bold")
    ax = fig.add_axes([0.10, 0.245, 0.82, 0.415])
    _series(ax, dependency_warnings, AMBER)
    _timeline_axis(ax, versions)
    ax.set_ylim(bottom=0, top=max(1, max(dependency_warnings) * 1.15))
    ax.fill_between(range(len(versions)), dependency_warnings, color=AMBER, alpha=0.08)
    _save(pdf, fig, "All recorded values shown. Version labels spaced for readability.")


def page_commit_log(pdf, meta_data):
    recent = meta_data[:MAX_COMMIT_HISTORY]
    _table_pages(pdf, "Version commit history", f"Latest {len(recent)} entries / newest first / full commit messages",
                 ["Version", "Commit ID", "Message"],
                 [[item["version"], item["commit_id"], item["message"]] for item in recent],
                 [0.12, 0.29, 0.59], "History")


def page_contributors(pdf, user_data):
    if not user_data:
        return
    ordered = sorted(user_data.items(), key=lambda item: item[1], reverse=True)
    leads = [(user, score) for user, score in ordered if score > 30]
    others = [(user, score) for user, score in ordered if score <= 30]
    for page_index in range(max(1, math.ceil(len(leads) / 3), math.ceil(len(others) / 10))):
        fig = _page("Project contributors", "Share of project contributions / lead contributors shown above", "People")
        for i, (user, score) in enumerate(leads[page_index * 3:page_index * 3 + 3]):
            x = 0.045 + i * 0.31
            _card(fig, (x, 0.62, 0.29, 0.16))
            fig.text(x + 0.02, 0.738, user, fontsize=11, weight="bold")
            fig.text(x + 0.02, 0.663, f"{score:.2f}%", fontsize=25, color=TEAL, weight="bold")
        chunk = others[page_index * 10:page_index * 10 + 10]
        if chunk:
            _card(fig, (0.045, 0.13, 0.91, 0.45))
            ax = fig.add_axes([0.22, 0.21, 0.65, 0.32])
            values = [value for _, value in chunk]
            ax.barh(range(len(chunk)), values, color=TEAL, height=0.48)
            ax.set_yticks(range(len(chunk)), [user for user, _ in chunk], fontsize=11)
            ax.set_ylim(len(chunk) - 0.4, -0.6)
            ax.set_xlim(0, max(values) * 1.2 if max(values) else 1)
            ax.xaxis.set_major_formatter(StrMethodFormatter("{x:g}%"))
            ax.grid(axis="x")
            ax.tick_params(length=0, pad=8)
            for i, value in enumerate(values):
                ax.annotate(f"{value:.2f}%", (value, i), xytext=(7, 0), textcoords="offset points",
                            va="center", fontsize=10, weight="bold", color=TEAL)
        _save(pdf, fig, "The bar chart shows contributors with a share of 30% or less.")


def _text_cards(pdf, title, subtitle, entries, section):
    """Flow complete lists into two columns, with continuation headings."""
    fig = None
    slot = 0
    for heading, items in entries:
        if fig is None:
            fig = _page(title, subtitle, section)
        lines = []
        for item in items:
            lines.extend(_wrap_text(fig, item, 0.415 * PAGE_WIDTH, size=9))
        lines = lines or ["No entries recorded."]
        for start in range(0, len(lines), 27):
            if fig is None:
                fig = _page(title, subtitle, section)
            x = 0.045 + slot * 0.465
            _card(fig, (x, 0.115, 0.445, 0.675))
            heading_lines = _wrap_text(fig, heading + (" / continued" if start else ""),
                                       0.405 * PAGE_WIDTH, size=11)
            fig.text(x + 0.02, 0.757, "\n".join(heading_lines), fontsize=11, weight="bold", va="top")
            fig.text(x + 0.02, 0.694, "\n".join(lines[start:start + 27]), fontsize=9,
                     color=MUTED, va="top", linespacing=1.4)
            slot += 1
            if slot == 2:
                _save(pdf, fig)
                fig, slot = None, 0
    if fig is not None:
        _save(pdf, fig)


def page_contributors_areas(pdf, contributors_areas):
    entries = [(f"{user} / {len(files)} file entries", sorted(files))
               for user, files in sorted(contributors_areas.items(), key=lambda item: (-len(item[1]), item[0].lower()))]
    _text_cards(pdf, "Contributors' file changes", "Complete recorded file lists / long paths wrap and continue onto the next card",
                entries, "People")


def visualize_device_metrics(pdf, data):
    records = [(device_type, device, version, metrics)
               for version, devices in data.items()
               for device_type, device_list in devices.items()
               for device, metrics in device_list.items()]
    # Stable sorts keep device types grouped, newest versions first, then device names.
    records.sort(key=lambda item: item[1].lower())
    records.sort(key=lambda item: Version(item[2]), reverse=True)
    records.sort(key=lambda item: item[0].lower())
    if not records:
        return
    time_metrics = sorted({key for *_, metrics in records for key in metrics if key.endswith("_ms")})
    device_types = sorted({record[0] for record in records})
    colors = {kind: COLORS[i % len(COLORS)] for i, kind in enumerate(device_types)}
    metrics_to_plot = [(key, "ms") for key in time_metrics] + [("mem_percent", "%"), ("fs_percent", "%")]
    titles = {"mem_percent": "Memory utilization", "fs_percent": "Filesystem utilization"}
    for metric, unit in metrics_to_plot:
        maximum = max((record[3].get(metric) or 0 for record in records), default=0)
        title = titles.get(metric, metric.removesuffix("_ms").replace("_", " ").capitalize())
        fig = _page(title, f"Device benchmarks / {len(records)} records / newest versions first within each device type", "Devices")
        # Preserve the usual row spacing as the number of records grows.
        fig.set_size_inches(PAGE_SIZE[0], PAGE_SIZE[1] * max(1, len(records) / 20))
        _card(fig, (0.045, 0.12, 0.91, 0.68))
        ax = fig.add_axes([0.36, 0.19, 0.49, 0.565])
        ax.set_yticks(range(len(records)), [f"{device} / {version} / {kind}" for kind, device, version, _ in records], fontsize=9)
        ax.set_ylim(len(records) - 0.4, -0.6)
        ax.set_xlim(0, max(1, maximum) * 1.3)
        ax.grid(axis="x")
        ax.tick_params(length=0, pad=7)
        ax.set_xlabel("Time (ms)" if unit == "ms" else "Usage (%)", fontsize=9)
        for i, (kind, _, _, values) in enumerate(records):
            value = values.get(metric)
            if value is None:
                text, value = "Not recorded", 0
            else:
                text = f"{value:g} {unit}"
                byte_key = {"mem_percent": "mem_used_byte", "fs_percent": "fs_used_byte"}.get(metric)
                if byte_key and byte_key in values:
                    text += f" / {values[byte_key] / 1024:.1f} KiB"
            ax.barh(i, value, color=colors[kind], height=0.5)
            ax.annotate(text, (value, i), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9)
        _save(pdf, fig, "Device type is included in each label. Missing measurements are marked explicitly.")
    _table_pages(pdf, "Device module inventory", "Complete loaded-module lists for each benchmark record",
                 ["Device / version", "Device type", "Loaded modules"],
                 [[f"{device} / {version}", kind, ", ".join(metrics.get("modules", [])) or "None recorded"]
                  for kind, device, version, metrics in records], [0.25, 0.18, 0.57], "Devices")


def _is_version_jsonn(filename):
    version_pattern = r'^\d+\.\d+\.\d+(?:-\d+)?\.json$'
    return re.match(version_pattern, filename)

def _ordered_file_list(folder_path):
    files = os.listdir(folder_path)
    valid_files = [f for f in files if _is_version_jsonn(f)]
    files_without_version =  [f for f in files if not _is_version_jsonn(f)]
    # Sort using Version from packaging
    sorted_files = sorted(valid_files, key=lambda f: Version(os.path.splitext(f)[0]))
    return sorted_files, files_without_version

def load_json_files(folder_path):
    """Load and parse JSON files from the given folder."""
    data = []
    extradata = {}
    version_files, additional_files = _ordered_file_list(folder_path)
    all_files = version_files + additional_files
    for file_name in all_files:  # Incremental version order
        if file_name.endswith(".json"):
            if _is_version_jsonn(file_name):
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, "r") as f:
                    content = json.load(f)
                    summary = content["summary"]
                    summary["version"] = file_name.replace(".json", "")
                    summary["core_refs"] = {f:l[1] for f, l in content["files"].items() if "LM_" not in f}
                    data.append(summary)
            else:
                if file_name == "contributions.json":
                    file_path = os.path.join(folder_path, file_name)
                    with open(file_path, "r") as f:
                        content = json.load(f)
                    extradata["contributors"] = content
                elif file_name == "devices_system_metrics.json":
                    file_path = os.path.join(folder_path, file_name)
                    with open(file_path, "r") as f:
                        content = json.load(f)
                    extradata["system_metrics"] = content
                else:
                    print(f"UNKNOWN JSON: {file_name}")
    return data, extradata

def load_meta_files(folder_path):
    """Load and parse .meta files from the given folder."""
    meta_data = []
    version_files, additional_files = _ordered_file_list(folder_path)
    all_files = version_files + additional_files
    for file_name in  all_files:  # Incremental version order
        if file_name.endswith(".meta"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = f.read().strip()
                if ": " in content:
                    commit_id, commit_message = content.split(": ", 1)
                    version = file_name.replace(".meta", "")
                    meta_data.append({"version": version, "commit_id": commit_id, "message": commit_message})
    return sorted(meta_data, key=lambda item: Version(item["version"]), reverse=True)

def load_release_versions(folder_path):
    release_versions = []
    try:
        with open(f"{folder_path}/release_versions.info", 'r') as f:
            release_versions = f.read().strip().split()
        release_versions = [v.replace("v", '').strip() for v in release_versions]
    except Exception as e:
        print("Error loading release_versions.info")
    return release_versions


def _summary_value(summary, key, default=0, index=0):
    value = summary.get(key, default)
    if isinstance(value, list):
        return value[index] if len(value) > index else default
    if index > 0:
        return default
    return value


def visualize_timeline(data, extradata, meta_data, highlighted_versions, output_pdf):
    """Generate timeline visualizations for all metrics and save to a PDF."""
    if not data:
        raise ValueError("No version summaries found; collect analysis_workdir inputs first.")
    versions = [d["version"] for d in data]

    # Extract data for each timeline
    core_lines = [d["core"][0] for d in data]
    core_files = [d["core"][1] for d in data]
    load_lines = [d["load"][0] for d in data]
    load_files = [d["load"][1] for d in data]
    package_lines = [_summary_value(d, "packages", 0, index=0) for d in data]
    package_counts = [_summary_value(d, "packages", 0, index=2) for d in data]
    core_scores = [d["core_score"] for d in data]
    load_scores = [d["load_score"] for d in data]
    dependency_warnings = [d["load_dep"][1] for d in data]
    contributors = extradata.get("contributors") or {}
    contributors_scores = contributors.get("scores") or {}
    contributors_areas = contributors.get("areas") or {}
    system_metrics = extradata.get("system_metrics")

    # Extract core_refs data per file
    all_files = sorted(set(f for d in data for f in d["core_refs"].keys()))
    core_refs_by_file = {f: [d["core_refs"].get(f, 0) for d in data] for f in all_files}

    with plt.rc_context(STYLE), PdfPages(output_pdf) as pdf:
        pdf.infodict().update(Title="micrOS engineering report",
                              Author="micrOS / DevToolKit",
                              Subject="Version evolution, contributors and device benchmarks")

        page_report_intro(pdf, versions, isinstance(system_metrics, dict))

        page_core_system(pdf, versions, core_files, highlighted_versions, core_lines)

        page_load_modules(pdf, versions, load_files, highlighted_versions, load_lines)

        page_packages(pdf, versions, package_counts, highlighted_versions, package_lines)

        page_core_system_refs(pdf, core_refs_by_file, versions)

        # Show developer contributions
        page_contributors(pdf, contributors_scores)
        page_contributors_areas(pdf, contributors_areas)

        page_pylint_scores(pdf, versions, core_scores, load_scores, highlighted_versions)

        page_dep_warnings(pdf, versions, dependency_warnings)

        if isinstance(system_metrics, dict):
            visualize_device_metrics(pdf, system_metrics)

        page_commit_log(pdf, meta_data)


def main():
    script_dir = Path(__file__).resolve().parent
    input_folder = script_dir / "analysis_workdir"
    output_pdf = script_dir / "timeline_visualization.pdf"

    # Load data
    data, extradata = load_json_files(input_folder)
    meta_data = load_meta_files(input_folder)
    release_versions = load_release_versions(input_folder)

    # Visualize data
    visualize_timeline(data, extradata, meta_data, release_versions, output_pdf)
    print(f"Timeline visualization saved to {output_pdf}")

if __name__ == "__main__":
    main()
