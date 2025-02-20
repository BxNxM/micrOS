import subprocess
import json

OUTPUT_JSON = "analysis_workdir/contributions.json"

def get_contributions():
    # Get the list of all contributors
    contributors = subprocess.check_output(
        "git shortlog -s -n --all", shell=True).decode('utf-8').strip().split("\n")

    total_lines = 0
    contributions = {}

    for contributor in contributors:
        count, name = contributor.strip().split("\t")
        count = int(count)

        # Get the number of lines added and deleted by the contributor
        stats = subprocess.check_output(
            f"git log --author='{name}' --pretty=tformat: --numstat", shell=True).decode('utf-8').strip().split("\n")

        lines_added = 0
        lines_removed = 0

        for line in stats:
            parts = line.split()
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                lines_added += int(parts[0])
                lines_removed += int(parts[1])

        lines_modified = lines_added + lines_removed

        contributions[name] = lines_modified
        total_lines += lines_modified

    # Calculate the contribution percentage
    contribution_scores = {name: (contrib / total_lines) * 100 for name, contrib in contributions.items()}

    return contribution_scores


def user_aliases(contribution_scores):
    aliases = {"Bán Marcell": 'BNM', "Kasza Kristof": 'KKristof452', "Kristóf Kasza": 'KKristof452'}
    for hide_key in aliases:
        score = contribution_scores[hide_key]
        group_key = aliases[hide_key]
        contribution_scores[group_key] += score
        del contribution_scores[hide_key]


if __name__ == "__main__":
    # Run the function and print results
    contribution_scores = get_contributions()
    user_aliases(contribution_scores)
    for contributor, score in contribution_scores.items():
        print(f"{contributor}: {score:.2f}%")

    print(f"Save contributors scores: {OUTPUT_JSON}")
    with open(OUTPUT_JSON, 'w') as f:
        json_cont = json.dumps(contribution_scores)
        f.write(json_cont)

