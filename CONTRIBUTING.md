# Contributing to discordforge-py

Thanks for your interest in contributing! Here's how to get started.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/discordforge-py
   cd discordforge-py
   ```
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

## Running Tests

```bash
pytest tests/
```

## Code Style

We use `ruff` for linting and formatting:

```bash
ruff check .
ruff format .
```

## Submitting a PR

- Keep PRs focused – one feature or fix per PR
- Make sure all tests pass
- Update the README if you're changing public API
- Reference any related issues in your PR description

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) when opening an issue.

## Questions?

Join our [Discord server](https://discord.gg/dfo) or open a [discussion](https://github.com/discordforge/discordforge-py/discussions).
