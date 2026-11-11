import sys
import os
from dulwich.repo import Repo
from dulwich.porcelain import push, branch_create

def main():
    if len(sys.argv) < 2:
        print("Usage: python push_to_github.py <github_repo_url>")
        print("Example: python push_to_github.py https://github.com/your-username/otto.git")
        sys.exit(1)

    remote_url = sys.argv[1]
    repo_path = os.path.abspath(os.path.dirname(__file__))
    repo = Repo(repo_path)
    
    print(f"Preparing to push to {remote_url}...")
    try:
        # Push current HEAD to main branch on remote
        push(repo_path, remote_url, refspecs=["refs/heads/master:refs/heads/main"])
        print("Successfully pushed to GitHub!")
    except Exception as e:
        print(f"Push failed or credentials required: {e}")
        print("If GitHub requires personal access token, use: https://<TOKEN>@github.com/username/repo.git")

if __name__ == "__main__":
    main()
