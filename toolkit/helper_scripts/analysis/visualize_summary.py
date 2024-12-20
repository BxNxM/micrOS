import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from textwrap import wrap

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

def visualize_timeline(data, meta_data, output_pdf):
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

        plt.title("Core System Size Evolution", fontweight="bold")
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

        plt.title("Load Modules Size Evolution", fontweight="bold")
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

        plt.title("Pylint Scores Evolution", fontweight="bold")
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

        plt.title("Load Dependency Warnings Evolution", fontweight="bold")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        #########################################################
        # Plot 5: Commit Log
        # Dynamically adjust figure height based on the number of rows
        rows = len(meta_data) + 1  # +1 for the header row
        fig_height = max(6, min(0.4 * rows, 50))  # Dynamic height scaling
        fig, ax = plt.subplots(figsize=(15, fig_height))  # Adjust height dynamically
        ax.axis('off')  # Hide axes for clean text visualization

        # Prepare data for visualization, with text wrapping for the "Message" column
        table_data = [["Version", "Commit ID", "Message"]]
        wrap_width = 60  # Maximum characters per line for wrapping
        for entry in meta_data:
            wrapped_message = "\n".join(wrap(entry["message"], wrap_width))  # Wrap the message text
            table_data.append([entry["version"], entry["commit_id"], wrapped_message])

        # Create the table and fit it to the page
        table = ax.table(
            cellText=table_data, colLabels=["Version", "Commit ID", "Message"], loc='center', cellLoc='left'
        )

        # Set font size dynamically based on the number of rows
        font_size = max(14, min(10, 200 / rows))  # Reduce font size for larger tables
        table.auto_set_font_size(True)
        #table.set_fontsize(font_size)

        # Adjust column widths
        table.auto_set_column_width(col=list(range(len(table_data[0]))))

        # Style the table
        for (row, col), cell in table.get_celld().items():
            if row == 0:  # Header row
                cell.set_text_props(weight="bold", color="white")
                cell.set_facecolor("#404040")
            else:
                cell.set_facecolor("#202020")  # Optional: style for data rows

        # Ensure the table fills the page
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Adjust spacing
        plt.title("Version Commit Log (beta)", fontweight="bold", fontsize=font_size + 2)
        pdf.savefig(fig)
        plt.close(fig)


def main():
    input_folder = "./analysis_workdir"  # Change to your folder path
    output_pdf = "timeline_visualization.pdf"

    # Load data
    data = load_json_files(input_folder)
    meta_data = load_meta_files(input_folder)

    # Visualize data
    visualize_timeline(data, meta_data, output_pdf)

    print(f"Timeline visualization saved to {output_pdf}")

if __name__ == "__main__":
    main()
