import subprocess
import json
import os

MYPATH = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MYPATH, "../../.."))
PACKAGES_REPO_PATH = os.path.join(REPO_ROOT, "micrOS/packages")
PACKAGES_PREFIX = "micrOS/packages"

OUTPUT_JSON = "analysis_workdir/contributions.json"
USER_ALIASES = {"Bán Marcell": 'BNM',
                "Kasza Kristof": 'KKristof452', "Kristóf Kasza": 'KKristof452', "Kristof Kasza": "KKristof452",
                "Florian": "fmandl"}

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
    contributor_list = set(contributors.keys())
    contributor_files = {}
    owner_contributions = {"BNM": [], "Bán Marcell": []}

    def _is_ignored_file():
        nonlocal modified_file
        if (modified_file.startswith("micrOS/client/sfuncman") or modified_file.startswith("release_info/sfuncman")
                or modified_file.endswith(".mpy")
                or modified_file.startswith("micrOS/release_info")):
            return True
        return False

    def _is_package_payload():
        nonlocal modified_file
        return "/package/" in modified_file and not modified_file.endswith((".mpy", ".pyc"))

    if os.path.isdir(PACKAGES_REPO_PATH):
        package_contributors = subprocess.check_output(
            "git shortlog -s -n --all", shell=True, cwd=PACKAGES_REPO_PATH).decode('utf-8').strip().split("\n")
        for contributor in package_contributors:
            if not contributor:
                continue
            _, name = contributor.strip().split("\t")
            contributor_list.add(name)

    for name in sorted(contributor_list):
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
        if os.path.isdir(PACKAGES_REPO_PATH):
            stats = subprocess.check_output(
                f"git log --author='{name}' --pretty=tformat: --numstat", shell=True,
                cwd=PACKAGES_REPO_PATH).decode('utf-8').strip().split("\n")
            for line in stats:
                parts = line.split()
                if len(parts) == 3:
                    modified_file = parts[2]
                    if not _is_package_payload():
                        continue
                    modified_files.add(f"{PACKAGES_PREFIX}/{modified_file}")
        if name in owner_contributions.keys():
            owner_contributions[name] = sorted(modified_files)
        else:
            contributor_files[name] = sorted(modified_files)
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
