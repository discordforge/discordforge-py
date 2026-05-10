## What does this PR do?

<!-- Brief description of the change -->

## Related issue

Closes #

## Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type check passes (`pyright discordforge/`)
- [ ] README updated (if public API changed)
- [ ] Added to CHANGELOG if applicable

---

## Release process (for maintainers)

Releases are handled by the `Release` workflow — do **not** bump versions manually in PRs.

1. Merge this PR to `main`
2. Go to **Actions → Release → Run workflow**
3. Choose `bump` (patch/minor/major) or set `custom_version`
4. Workflow bumps `pyproject.toml` + `__init__.py`, tags, and creates a GitHub Release
5. The Release event triggers `publish.yml` which waits for maintainer approval before uploading to PyPI
