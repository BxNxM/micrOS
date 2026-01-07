import subprocess
import json

OUTPUT_JSON = "analysis_workdir/contributions.json"
USER_ALIASES = {"Bán Marcell": 'BNM', "Kasza Kristof": 'KKristof452', "Kristóf Kasza": 'KKristof452', "Kristof Kasza": "KKristof452"}

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


def get_contributor_areas(contributors:dict):
    contributor_list = list(contributors.keys())
    contributor_files = {}
    owner_contributions = {"BNM": [], "Bán Marcell": []}

    def _is_ignored_file():
        nonlocal modified_file
        if (modified_file.startswith("micrOS/client/sfuncman") or modified_file.startswith("release_info/sfuncman")
                or modified_file.endswith(".mpy")
                or modified_file.startswith("micrOS/release_info")):
            return True
        return False

    for name in contributor_list:
        stats = subprocess.check_output(
            f"git log --author='{name}' --pretty=tformat: --numstat", shell=True).decode('utf-8').strip().split("\n")
        modified_files = set()
        for line in stats:
            parts = line.split()
            if len(parts) == 3:
                modified_file = parts[2]
                if _is_ignored_file():
                    continue
                modified_files.add(modified_file)
        if name in owner_contributions.keys():
            owner_contributions[name] = list(modified_files)
        else:
            contributor_files[name] = list(modified_files)
    return contributor_files, owner_contributions


def user_aliases(contribution_scores):
    aliases = USER_ALIASES
    for hide_key in aliases:
        score = contribution_scores.get(hide_key)
        if score is None:
            continue
        group_key = aliases[hide_key]
        contribution_scores[group_key] += score
        del contribution_scores[hide_key]


if __name__ == "__main__":
    # Run the function and print results
    contribution_scores = get_contributions()
    contributor_files, owner_contributions = get_contributor_areas(contribution_scores)
    user_aliases(contribution_scores)
    user_aliases(contributor_files)

    print("Contributors")
    for contributor, score in contribution_scores.items():
        print(f"{contributor}: {score:.2f}%")

    #print("Contributor file modifications:")
    #for contributor, files in contributor_files.items():
    #    print(f"{contributor}: {files}")

    data_dict = {"scores": contribution_scores, "areas": contributor_files}
    print(f"Save contributors scores: {OUTPUT_JSON}")
    with open(OUTPUT_JSON, 'w') as f:
        json_cont = json.dumps(data_dict, indent=4)
        f.write(json_cont)

