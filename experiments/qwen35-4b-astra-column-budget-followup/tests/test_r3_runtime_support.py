def trust_test_git_root(monkeypatch,root):
    """Trust this synthetic repo only, including on uid-mapped T7 mounts."""
    import os
    count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
    monkeypatch.setenv('GIT_CONFIG_COUNT',str(count+1))
    monkeypatch.setenv(f'GIT_CONFIG_KEY_{count}','safe.directory')
    monkeypatch.setenv(f'GIT_CONFIG_VALUE_{count}',str(root))


def git_commit_public(layout, name):
    import subprocess
    from r3_runtime.commitments import public_path
    root = layout.project_root
    def git(*args):
        return subprocess.run(["git", "-c", 'safe.directory='+str(root), "-C", str(root), *args], check=True, capture_output=True)
    if not (root / ".git").exists():
        git("init", "-q")
        git("config", "user.email", "synthetic@example.invalid")
        git("config", "user.name", "Synthetic CPU Fixture")
    git("add", "--", str(public_path(layout, name).relative_to(root)))
    git("commit", "-q", "--allow-empty", "-m", "Synthetic public commitment")
