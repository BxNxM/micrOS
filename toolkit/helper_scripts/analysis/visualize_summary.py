import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from textwrap import wrap

TITLE_FONT_SIZE=18
DARK_YELLOW="#B8860B"

def load_json_files(folder_path):
    """Load and parse JSON files from the given folder."""
    data = []
    for file_name in sorted(os.listdir(folder_path)):  # Incremental version order
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = json.load(f)
                summary = content["summary"]
                summary["version"] = file_name.replace(".json", "")
                data.append(summary)
    return data

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
        release_versions = [ v.replace("v", '').strip() for v in release_versions ]
    except Exception as e:
        print("Error loading release_versions.info")
    return release_versions


def visualize_timeline(data, meta_data, highlighted_versions, output_pdf):
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

    with PdfPages(output_pdf) as pdf:
        # Settings for the gray background
        plt.style.use('dark_background')

        #########################################################
        # Plot 1: Core System Lines and File Count

        fig, ax1 = plt.subplots(figsize=(15, 8))  # Wider figure for better version visibility
        ax1.plot(versions, core_lines, label="Lines of Code", color="purple", marker="o")
        ax1.set_ylabel("Lines of Code", color="purple")
        ax1.set_xlabel("Versions")
        ax1.tick_params(axis='y', labelcolor="purple")
        ax1.set_xticks(range(len(versions)))
        ax1.set_xticklabels(versions, rotation=90, fontsize=8)
        ax1.grid(True, linestyle="--", alpha=0.1)

        # Highlight specific versions
        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax1.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        # Annotate the last data point
        ax1.annotate(f'{core_lines[-1]}',
                     xy=(len(versions) - 1, core_lines[-1]),
                     xytext=(len(versions) + 0.5, core_lines[-1]),  # Minimal offset
                     color="purple", fontsize=9, arrowprops=dict(arrowstyle="->", color="purple"))

        ax2 = ax1.twinx()
        ax2.plot(versions, core_files, label="File Count", color="teal", marker="x")
        ax2.set_ylabel("File Count", color="teal")
        ax2.tick_params(axis='y', labelcolor="teal")
        ax2.grid(False)

        # Annotate the last data point
        ax2.annotate(f'{core_files[-1]}',
                     xy=(len(versions) - 1, core_files[-1]),
                     xytext=(len(versions) + 0.5, core_files[-1]),  # Minimal offset
                     color="teal", fontsize=9, arrowprops=dict(arrowstyle="->", color="teal"))

        ax1.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
        ax2.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

        plt.title("Core System Size Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        #########################################################
        # Plot 2: Load Modules Lines and File Count
        fig, ax1 = plt.subplots(figsize=(15, 8))
        ax1.plot(versions, load_lines, label="Lines of code", color="purple", marker="o")
        ax1.set_ylabel("Lines of Code", color="purple")
        ax1.set_xlabel("Versions")
        ax1.tick_params(axis='y', labelcolor="purple")
        ax1.set_xticks(range(len(versions)))
        ax1.set_xticklabels(versions, rotation=90, fontsize=8)
        ax1.grid(True, linestyle="--", alpha=0.1)

        # Highlight specific versions
        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax1.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        # Annotate the last data point
        ax1.annotate(f'{load_lines[-1]}',
                     xy=(len(versions) - 1, load_lines[-1]),
                     xytext=(len(versions) + 0.5, load_lines[-1]),  # Minimal offset
                     color="purple", fontsize=9, arrowprops=dict(arrowstyle="->", color="purple"))

        ax2 = ax1.twinx()
        ax2.plot(versions, load_files, label="File Count", color="teal", marker="x")
        ax2.set_ylabel("File Count", color="teal")
        ax2.tick_params(axis='y', labelcolor="teal")
        ax2.grid(False)

        # Annotate the last data point
        ax2.annotate(f'{load_files[-1]}',
                     xy=(len(versions) - 1, load_files[-1]),
                     xytext=(len(versions) + 0.5, load_files[-1]-1),  # Minimal offset
                     color="teal", fontsize=9, arrowprops=dict(arrowstyle="->", color="teal"))

        ax1.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
        ax2.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

        plt.title("Load Modules Size Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 3: Core and Load Scores
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(versions, core_scores, label="Core Score", color="brown", marker="o")
        ax.plot(versions, load_scores, label="Load Score", color="grey", marker="x")
        ax.set_ylabel("Scores")
        ax.set_xlabel("Versions")
        ax.set_xticks(range(len(versions)))
        ax.set_xticklabels(versions, rotation=90, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.1)
        ax.legend(loc="upper center", fontsize=10, bbox_to_anchor=(0.5, 1.12), ncol=2)

        # Highlight specific versions
        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        plt.title("Pylint Scores Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        #########################################################
        # Plot 4: Dependency Warnings
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

        #########################################################
        # Plot 5: Commit Log
        # Dynamically adjust the figure size and ensure the table fits within the page
        # Plot 5: Commit Log
        # Dynamically adjust the figure size to ensure the table fits all data lines
        rows = len(meta_data) + 1  # +1 for the header row
        row_height = 0.2  # Height for each row in the table
        fig_width = 15  # Fixed width
        fig_height = max(8, rows * row_height)  # Dynamically adjust height based on the number of rows

        # Create the figure with adjusted height
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')  # Hide axes for clean text visualization

        # Prepare data for visualization with wrapped text
        table_data = [["Version", "Commit ID", "Message"]]
        wrap_width = 120  # Maximum characters per line for wrapping

        for entry in meta_data:
            wrapped_message = "\n".join(wrap(entry["message"], wrap_width))  # Wrap the message text
            table_data.append([entry["version"], entry["commit_id"], wrapped_message])

        # Create the table
        table = ax.table(
            cellText=table_data, loc='center', cellLoc='left', colWidths=[0.15, 0.3, 0.55]  # Adjust column widths
        )

        # Adjust row heights and font size dynamically
        for (row, col), cell in table.get_celld().items():
            cell.set_fontsize(10)  # Set font size
            if row == 0:  # Header row
                cell.set_text_props(weight="bold", color="white")
                cell.set_facecolor("#404040")
            else:
                cell.set_facecolor("#202020")  # Optional: style for data rows

        # Adjust table layout to fit the full figure
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Adjust margins
        plt.title("Version Commit Log (beta)", fontweight="bold", fontsize=16)  # Adjust title font size
        pdf.savefig(fig)  # Save to PDF
        plt.close(fig)


def main():
    input_folder = "./analysis_workdir"  # Change to your folder path
    output_pdf = "timeline_visualization.pdf"

    # Load data
    data = load_json_files(input_folder)
    meta_data = load_meta_files(input_folder)
    release_versions = load_release_versions(input_folder)

    # Visualize data
    visualize_timeline(data, meta_data, release_versions, output_pdf)

    print(f"Timeline visualization saved to {output_pdf}")

if __name__ == "__main__":
    main()
