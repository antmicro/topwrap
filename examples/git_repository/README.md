Copyright (c) 2026 [Antmicro](https://antmicro.com)

# Example of a project with a repository loaded from a git URL

This example is functionally identical to the [user repository example](../user_repository), except that instead of
referencing a local `repo:` directory, `topwrap.yaml` loads the same repository straight from its git URL using the
`git:` resource scheme:

```yaml
repositories:
  my_repo: git[main|examples/user_repository/repo]:https://github.com/antmicro/topwrap.git
```

- `main` is the branch to check out (a tag or commit SHA also works).
- `examples/user_repository/repo` is the subdirectory inside the cloned repository that contains the `cores/` and
  `interfaces/` folders. Both arguments are optional; omitting either just checks out the default branch and/or uses
  the repository root.

The repository is cloned into a persistent local cache (by default under `~/.cache/topwrap/git_repos/`, or
`$XDG_CACHE_HOME/topwrap/git_repos/`), so it's only downloaded once — later runs reuse the cached clone.

See the [resource path syntax](https://antmicro.github.io/topwrap/description_files.html#resource-path-syntax)
documentation for more details on the `git:` scheme.
