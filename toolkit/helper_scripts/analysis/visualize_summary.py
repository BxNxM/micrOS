import os
import json
import re
from pprint import pprint

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from textwrap import wrap

TITLE_FONT_SIZE = 18
DARK_YELLOW = "#B8860B"
MAX_COMMIT_HISTORY = 60

#####################################
#           HELPER FUNCTIONS        #
#####################################
def truncate_message(message, wrap_width, max_lines):
    """
    Wrap the message text to a given width and limit it to max_lines.
    If the message is longer than allowed, the last line is truncated with an ellipsis.
    """
    lines = wrap(message, wrap_width)
    if len(lines) > max_lines:
        # Take the first max_lines-1 full lines and then truncate the last line
        truncated_last_line = lines[max_lines - 1]
        if len(truncated_last_line) > wrap_width - 3:
            truncated_last_line = truncated_last_line[:wrap_width - 3] + '...'
        return "\n".join(lines[:max_lines - 1] + [truncated_last_line])
    else:
        return "\n".join(lines)

def _is_version_jsonn(filename):
    version_pattern = r'^\d+\.\d+\.\d+(?:-\d+)?\.json$'
    return re.match(version_pattern, filename)

def load_json_files(folder_path):
    """Load and parse JSON files from the given folder."""
    data = []
    extradata = {}
    for file_name in sorted(os.listdir(folder_path)):  # Incremental version order
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
    for file_name in sorted(os.listdir(folder_path)):  # Incremental version order
        if file_name.endswith(".meta"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = f.read().strip()
                if ": " in content:
                    commit_id, commit_message = content.split(": ", 1)
                    version = file_name.replace(".meta", "")
                    meta_data.append({"version": version, "commit_id": commit_id, "message": commit_message})
    return meta_data

def load_release_versions(folder_path):
    release_versions = []
    try:
        with open(f"{folder_path}/release_versions.info", 'r') as f:
            release_versions = f.read().strip().split()
        release_versions = [v.replace("v", '').strip() for v in release_versions]
    except Exception as e:
        print("Error loading release_versions.info")
    return release_versions


#####################################
#                PAGES              #
#####################################
def page_core_system(pdf, versions, core_files, highlighted_versions, core_lines):
    #########################################################
    # Plot 1: Core System – File Count (left) and Lines of Code (right)
    fig, ax_left = plt.subplots(figsize=(15, 8))
    # Left y-axis: File Count (teal)
    ax_left.plot(versions, core_files, label="File Count", color="teal", marker="x")
    ax_left.set_ylabel("File Count", color="teal")
    ax_left.tick_params(axis='y', labelcolor="teal")
    ax_left.set_xlabel("Versions")
    ax_left.set_xticks(range(len(versions)))
    ax_left.set_xticklabels(versions, rotation=90, fontsize=8)
    ax_left.grid(True, linestyle="--", alpha=0.1)

    # Highlight specific versions
    for idx, version in enumerate(versions):
        if version in highlighted_versions:
            ax_left.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

    # Annotate the last file count data point with fixed offset (10 pts to the right)
    ax_left.annotate(f'{core_files[-1]}',
                     xy=(len(versions) - 1, core_files[-1]),
                     xytext=(10, 0), textcoords='offset points',
                     color="teal", fontsize=9,
                     arrowprops=dict(arrowstyle="->", color="teal"))

    # Right y-axis: Lines of Code (purple)
    ax_right = ax_left.twinx()
    ax_right.plot(versions, core_lines, label="Lines of Code", color="purple", marker="o")
    ax_right.set_ylabel("Lines of Code", color="purple")
    ax_right.tick_params(axis='y', labelcolor="purple")

    # Annotate the last line count data point with fixed offset (10 pts to the right)
    ax_right.annotate(f'{core_lines[-1]}',
                      xy=(len(versions) - 1, core_lines[-1]),
                      xytext=(10, 0), textcoords='offset points',
                      color="purple", fontsize=9,
                      arrowprops=dict(arrowstyle="->", color="purple"))

    ax_left.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
    ax_right.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

    plt.title("Core System Evolution: File Count & Lines of Code", fontweight="bold", fontsize=TITLE_FONT_SIZE)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def page_load_modules(pdf, versions, load_files, highlighted_versions, load_lines):
    #########################################################
    # Plot 2: Load Modules – File Count (left) and Lines of Code (right)
    fig, ax_left = plt.subplots(figsize=(15, 8))
    # Left y-axis: File Count (teal)
    ax_left.plot(versions, load_files, label="File Count", color="teal", marker="x")
    ax_left.set_ylabel("File Count", color="teal")
    ax_left.tick_params(axis='y', labelcolor="teal")
    ax_left.set_xlabel("Versions")
    ax_left.set_xticks(range(len(versions)))
    ax_left.set_xticklabels(versions, rotation=90, fontsize=8)
    ax_left.grid(True, linestyle="--", alpha=0.1)

    # Highlight specific versions
    for idx, version in enumerate(versions):
        if version in highlighted_versions:
            ax_left.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

    # Adjust annotation offsets so labels don't overlap:
    # For the file count (left axis), move upward; for lines (right axis), move downward.
    ax_left.annotate(f'{load_files[-1]}',
                     xy=(len(versions) - 1, load_files[-1]),
                     xytext=(10, 10), textcoords='offset points',
                     color="teal", fontsize=9,
                     arrowprops=dict(arrowstyle="->", color="teal"))

    # Right y-axis: Lines of Code (purple)
    ax_right = ax_left.twinx()
    ax_right.plot(versions, load_lines, label="Lines of Code", color="purple", marker="o")
    ax_right.set_ylabel("Lines of Code", color="purple")
    ax_right.tick_params(axis='y', labelcolor="purple")

    ax_right.annotate(f'{load_lines[-1]}',
                      xy=(len(versions) - 1, load_lines[-1]),
                      xytext=(10, -10), textcoords='offset points',
                      color="purple", fontsize=9,
                      arrowprops=dict(arrowstyle="->", color="purple"))

    ax_left.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
    ax_right.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

    plt.title("Load Modules Evolution: File Count & Lines of Code", fontweight="bold", fontsize=TITLE_FONT_SIZE)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def page_core_system_refs(pdf, core_refs_by_file, versions):
    #########################################################
    # Plot 3: Core References Evolution per File

    skip_if_ref_under = 3
    excluded_files = []
    fig, ax = plt.subplots(figsize=(15, 8))
    for file, refs in core_refs_by_file.items():
        if refs[-1] <= skip_if_ref_under:
            excluded_files.append(f"{file} ({refs[-1]})")
            continue
        ax.plot(versions, refs, marker="o", label=file)
    ax.set_ylabel("Core References Count")
    ax.set_xlabel("Versions")
    ax.set_xticks(range(len(versions)))
    ax.set_xticklabels(versions, rotation=90, fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.1)
    ax.set_xlim([-0.5, len(versions) + 20])  # Extend x-axis to make space for annotations
    # Annotate the last data point of each file with its filename and value
    for file, refs in core_refs_by_file.items():
        last_index = len(versions) - 1
        last_value = refs[-1]
        if last_value <= skip_if_ref_under:
            continue
        ax.annotate(f"{file} ({last_value})",
                    xy=(last_index, last_value),
                    xytext=(15, 0), textcoords='offset points',
                    fontsize=8, color='white',
                    verticalalignment='center', horizontalalignment='left')
    # Display excluded files list
    if excluded_files:
        excluded_text = "\n".join(excluded_files)
        ax.text(len(versions) + 10, max(max(core_refs_by_file.values(), key=max)) / 4,
                f"Excluded Files:\n{excluded_text}", fontsize=8, color='white',
                verticalalignment='center', horizontalalignment='left')
    plt.title("Core References Evolution Per File", fontweight="bold", fontsize=TITLE_FONT_SIZE)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def page_pylint_scores(pdf, versions, core_scores, load_scores, highlighted_versions):
    #########################################################
    # Plot 4: Core and Load Scores
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot(versions, core_scores, label="Core Score", color="brown", marker="o")
    ax.plot(versions, load_scores, label="Load Score", color="grey", marker="x")
    ax.set_ylabel("Scores")
    ax.set_xlabel("Versions")
    ax.set_xticks(range(len(versions)))
    ax.set_xticklabels(versions, rotation=90, fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.1)
    ax.legend(loc="upper center", fontsize=10, bbox_to_anchor=(0.5, 1.12), ncol=2)

    for idx, version in enumerate(versions):
        if version in highlighted_versions:
            ax.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

    plt.title("Pylint Scores Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def page_dep_warnings(pdf, versions, dependency_warnings):
    #########################################################
    # Plot 5: Dependency Warnings
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot(versions, dependency_warnings, label="Dependency Warnings", color="brown", marker="o")
    ax.set_ylabel("Warnings")
    ax.set_xlabel("Versions")
    ax.set_xticks(range(len(versions)))
    ax.set_xticklabels(versions, rotation=90, fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.1)
    ax.legend(loc="upper center", fontsize=10, bbox_to_anchor=(0.5, 1.12), ncol=2)

    plt.title("Load Dependency Warnings Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def page_commit_log(pdf, meta_data):
    #########################################################
    # Plot 6: Commit Log (Table fitted to page height with text truncation)
    wrap_width = 105  # Maximum characters per line for wrapping
    max_lines = 1  # Maximum number of lines allowed per commit message cell
    meta_data = meta_data[-MAX_COMMIT_HISTORY:]  # Set last 40 lines of comments
    table_data = [["Version", "Commit ID", "Message"]]
    for entry in meta_data:
        truncated_message = truncate_message(entry["message"], wrap_width, max_lines)
        table_data.append([entry["version"], entry["commit_id"], truncated_message])

    num_rows = len(table_data)

    # Set figure size to fill most of the PDF page (adjust as needed)
    fig, ax = plt.subplots(figsize=(15, 11))
    ax.axis('off')  # Hide axes for a clean table look

    # Create the table; using loc='center' so we can later force cell heights
    table = ax.table(cellText=table_data,
                     loc='center',
                     cellLoc='left',
                     colWidths=[0.06, 0.3, 0.64])

    # Force a fixed font size for clarity
    font_size = 12 if len(meta_data) < 10 else 10
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)

    # Adjust each cell’s height so that the table fits the full page height.
    # We leave a small vertical margin (here 0.90 of the figure height is used for the table).
    cell_height = 1 / num_rows
    for key, cell in table.get_celld().items():
        cell.set_height(cell_height)
        cell.set_edgecolor("gray")
        cell.get_text().set_color("white")
        # Header formatting
        if key[0] == 0:
            cell.set_facecolor("#404040")
            cell.set_text_props(weight="bold")
        else:
            cell.set_facecolor("#202020")

    # Adjust margins so that the table fills the entire figure height.
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.title(f"Version Commit History (last {MAX_COMMIT_HISTORY})", fontweight="bold", fontsize=16)
    pdf.savefig(fig)
    plt.close(fig)


def page_contributors(pdf, user_data):
    #########################################################
    # Plot: Contributors' Contributions
    #########################################################
    master_contributors = {u: s for u, s in user_data.items() if s > 30}
    minor_contributors = {u: s for u, s in user_data.items() if s <= 30}

    # Bar chart for minor contributors
    if minor_contributors:
        users, contributions = zip(*sorted(minor_contributors.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(15, 8))
        bars = ax.bar(users, contributions, color="steelblue")

        # Highlight the owner distinctly and separate major vs minor contributors
        owner_threshold = max(contributions) * 0.7  # Define a threshold for major contributors
        for bar, (user, contribution) in zip(bars, minor_contributors.items()):
            if contribution == max(contributions):
                bar.set_color("darkred")  # Highlight the owner
            elif contribution >= owner_threshold:
                bar.set_color("darkorange")  # Highlight major contributors
            else:
                bar.set_alpha(0.5)  # Fade minor contributors
            # Annotate each bar with the score value
            ax.annotate(f"{contribution:.2f}%", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha='center', va='top', fontsize=10, fontweight='bold', color='black', xytext=(0, -5),
                        textcoords='offset points')

        ax.set_ylabel("Contribution (%)")
        ax.set_xlabel("Contributors")
        ax.set_xticks(range(len(users)))
        ax.set_xticklabels(users, rotation=45, ha="right", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.3)

        plt.title("Project Contributors", fontweight="bold", fontsize=14)

        # Annotate master contributors at the top of the chart
        master_text = "\n".join([f"{user}: {score:.2f}%" for user, score in master_contributors.items()])
        ax.text(0.5, 1.15, master_text, ha='center', va='top', fontsize=12, fontweight='bold', transform=ax.transAxes,
                bbox=dict(facecolor='white', alpha=0.6))

        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


def page_contributors_areas(pdf, contributors_areas):
    """
    Create a PDF page that lists each contributor's modified files in separate columns.
    Each column displays the contributor's name in bold at the top and, after an empty line,
    an alphabetical list of the files they modified.

    Parameters:
        pdf: A PdfPages object from matplotlib.backends.backend_pdf used to save the figure.
        contributors_areas: A dict mapping each contributor's username to a list of file paths.
    """
    # Get a sorted list of contributors to maintain consistent order
    contributors = list(contributors_areas.keys())
    num_contributors = len(contributors)

    # Create a subplot for each contributor
    fig, axs = plt.subplots(1, num_contributors, figsize=(15, 10))
    # When there is only one contributor, axs is not a list
    if num_contributors == 1:
        axs = [axs]

    for ax, user in zip(axs, contributors):
        # Sort the file list alphabetically for the current contributor
        files_sorted = sorted(contributors_areas[user])
        # Display the username in bold at the top
        ax.text(0.05, 0.95, user, transform=ax.transAxes,
                va="top", ha="left", fontsize=12, family="monospace", fontweight="bold")
        # Leave an empty line and list the files below in alphabetical order
        ax.text(0.05, 0.90, "\n".join(files_sorted), transform=ax.transAxes,
                va="top", ha="left", fontsize=10, family="monospace")
        ax.axis("off")  # Hide axis lines and ticks

    # Add an overall title for the page
    fig.suptitle("Contributors' File Changes", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    # Save the page to the PDF and close the figure
    pdf.savefig(fig)
    plt.close(fig)


def visualize_device_metrics(pdf, data):

    # Collect all relevant metrics dynamically
    time_metrics = set()
    for devices in data.values():
        for device_list in devices.values():
            for metrics in device_list.values():
                for key in metrics.keys():
                    if key.endswith('_ms'):
                        time_metrics.add(key)

    num_plots = len(time_metrics) + 2  # +2 for memory and filesystem plots

    # Ensure the number of subplots matches the number of metrics
    fig, axes = plt.subplots(num_plots, 1, figsize=(15, 6 * num_plots))
    if num_plots == 1:
        axes = [axes]  # Ensure iterable for a single metric case

    # Prepare data structures
    device_types = {}
    for version, devices in data.items():
        for device_type, device_list in devices.items():
            if device_type not in device_types:
                device_types[device_type] = []
            for device, metrics in device_list.items():
                device_types[device_type].append((f"{device}:{version}", metrics))

    # Plot all _ms metrics dynamically
    for i, metric in enumerate(sorted(time_metrics)):  # Sort for consistency
        ax = axes[i]
        ax.set_title(f"{metric.replace('_', ' ').title()} by Device Type")
        for device_type, devices in device_types.items():
            values = [d[1].get(metric, 0) for d in devices]
            labels = [d[0] for d in devices]
            bars = ax.bar(labels, values, label=device_type)
            # Annotate each bar with the exact value
            for bar, value in zip(bars, values):
                ax.annotate(f"{value} ms",
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.set_ylabel("Time (ms)")
        ax.legend()
        ax.tick_params(axis='x', rotation=45)

    # Memory Utilization Plot with modules list annotation
    ax = axes[len(time_metrics)]
    ax.set_title("Memory Utilization by Device Type")
    for device_type, devices in device_types.items():
        mem_usage = [d[1].get("mem_percent", 0) for d in devices]
        mem_used = [d[1].get("mem_used_byte", 0) / 1024 for d in devices]  # Convert bytes to KB
        labels = [d[0] for d in devices]
        bars = ax.bar(labels, mem_usage, label=device_type)
        for i, bar in enumerate(bars):
            kb_value = mem_used[i]
            modules = devices[i][1].get("modules", [])
            modules_str = ",\n".join(modules)
            annotation_text = f"{kb_value:.1f} KB\nModules({len(modules)}):\n{modules_str}"
            ax.annotate(annotation_text,
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
    ax.set_ylabel("Memory Usage (%)")
    ax.set_ylim(0, 110)
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    # Filesystem Utilization Plot
    ax = axes[len(time_metrics) + 1]
    ax.set_title("Filesystem Utilization by Device Type")
    for device_type, devices in device_types.items():
        fs_usage = [d[1].get("fs_percent", 0) for d in devices]
        fs_used = [d[1].get("fs_used_byte", 0) / 1024 for d in devices]  # Convert bytes to KB
        labels = [d[0] for d in devices]
        bars = ax.bar(labels, fs_usage, label=device_type)
        # Annotate each bar with KB usage
        for bar, value in zip(bars, fs_used):
            ax.annotate(f"{value:.1f} KB\n55+ Modules",
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.set_ylabel("Filesystem Usage (%)")
    ax.set_ylim(0, 80)
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    for ay in axes:
        ay.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Save the figure
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


#####################################
#            MAIN PDF WRITER        #
#####################################

def visualize_timeline(data, extradata, meta_data, highlighted_versions, output_pdf):
    """Generate timeline visualizations for all metrics and save to a PDF."""
    versions = [d["version"] for d in data]

    # Extract data for each timeline
    core_lines = [d["core"][0] for d in data]
    core_files = [d["core"][1] for d in data]
    load_lines = [d["load"][0] for d in data]
    load_files = [d["load"][1] for d in data]
    core_scores = [d["core_score"] for d in data]
    load_scores = [d["load_score"] for d in data]
    dependency_warnings = [d["load_dep"][1] for d in data]
    contributors = extradata.get("contributors")
    contributors_scores = contributors.get("scores")
    contributors_areas = contributors.get("areas")
    system_metrics = extradata.get("system_metrics")

    # Extract core_refs data per file
    all_files = sorted(set(f for d in data for f in d["core_refs"].keys()))
    core_refs_by_file = {f: [d["core_refs"].get(f, 0) for d in data] for f in all_files}

    with PdfPages(output_pdf) as pdf:
        # Use dark background style
        plt.style.use('dark_background')

        #########################################################
        # Plot 1: Core System – File Count (left) and Lines of Code (right)
        page_core_system(pdf, versions, core_files, highlighted_versions, core_lines)

        #########################################################
        # Plot 2: Load Modules – File Count (left) and Lines of Code (right)
        page_load_modules(pdf, versions, load_files, highlighted_versions, load_lines)

        #########################################################
        # Plot 3: Core References Evolution per File
        page_core_system_refs(pdf, core_refs_by_file, versions)

        #########################################################
        # Show developer contributions
        page_contributors(pdf, contributors_scores)
        page_contributors_areas(pdf, contributors_areas)

        #########################################################
        # Plot 4: Core and Load Scores
        page_pylint_scores(pdf, versions, core_scores, load_scores, highlighted_versions)

        #########################################################
        # Plot 5: Dependency Warnings
        page_dep_warnings(pdf, versions, dependency_warnings)

        #########################################################
        # Plot 6: Commit Log (Table fitted to page height with text truncation)
        page_commit_log(pdf, meta_data)

        sys_metrics_data = system_metrics
        sys_metrics_ok = isinstance(system_metrics, dict)
        if sys_metrics_ok:
            try:
                visualize_device_metrics(pdf, sys_metrics_data)
            except Exception as e:
                print(f"(beta) Cannot render system test metrics: {e}")


def main():
    input_folder = "./analysis_workdir"  # Change to your folder path
    output_pdf = "timeline_visualization.pdf"

    # Load data
    data, extradata = load_json_files(input_folder)
    meta_data = load_meta_files(input_folder)
    release_versions = load_release_versions(input_folder)

    # Visualize data
    visualize_timeline(data, extradata, meta_data, release_versions, output_pdf)
    print(f"Timeline visualization saved to {output_pdf}")

if __name__ == "__main__":
    main()
