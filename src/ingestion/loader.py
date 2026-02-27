import os
import shutil
from git import Repo
from src.core.base import BaseLoader

class GitLoader(BaseLoader):
    def load(self, repo_url: str, target_path: str) -> str:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_full_path = os.path.join(target_path, repo_name)
        
        if os.path.exists(repo_full_path):
            print(f"Repository {repo_name} already exists at {repo_full_path}. Skipping clone.")
            return repo_full_path
            
        print(f"Cloning {repo_url} to {repo_full_path}...")
        try:
            Repo.clone_from(repo_url, repo_full_path)
        except Exception as e:
            if os.path.exists(repo_full_path): shutil.rmtree(repo_full_path)
            raise ValueError(f"Failed to clone repository. Ensure it's a valid public base Git URL. (Error: {str(e)})")
        return repo_full_path

    def get_branches(self, repo_path: str):
        """Returns a list of branches for the given repo."""
        try:
            repo = Repo(repo_path)
            # Fetch remote branches to ensure we see everything
            # (only if origin exists, to be safe)
            if 'origin' in repo.remotes:
                repo.remotes.origin.fetch()
            
            # List remote branches (e.g., origin/main, origin/dev)
            branches = [r.name for r in repo.remote().refs] 
            
            # Clean up: Remove 'origin/HEAD' and duplicates
            clean_branches = []
            seen = set()
            for b in branches:
                if 'HEAD' in b: continue  # Skip the HEAD pointer
                clean_branches.append(b)
                
            return clean_branches
        except Exception as e:
            return [f"Error fetching branches: {str(e)}"]

    def get_diff(self, repo_path: str, branch_a: str, branch_b: str) -> str:
        """Returns the git diff text between two branches."""
        try:
            repo = Repo(repo_path)
            # Create a diff between the two references
            # We use distinct commits to avoid ambiguity
            diff_index = repo.git.diff(branch_a, branch_b, unified=3)
            return diff_index
        except Exception as e:
            return f"Error computing diff: {str(e)}"
