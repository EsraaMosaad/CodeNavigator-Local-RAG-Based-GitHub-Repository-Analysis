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
        Repo.clone_from(repo_url, repo_full_path)
        return repo_full_path
