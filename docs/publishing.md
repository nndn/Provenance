# Publishing

`provenance-cli` is published to PyPI. Releases are built and published with
uv; the normal path is fully automated via GitHub trusted publishing.

## Release flow

1. Bump `version` in `pyproject.toml`, refresh the lockfile, commit:

   ```sh
   uv lock
   git commit -am "release: v0.2.0"
   ```

2. Tag and push:

   ```sh
   git tag v0.2.0
   git push origin main v0.2.0
   ```

3. Create the GitHub release (Releases → Create a new release → choose the
   tag). Publishing the release triggers
   `.github/workflows/publish-pypi.yml`, which runs `uv build` and
   `uv publish` using PyPI trusted publishing — the workflow authenticates
   with the GitHub OIDC token (`id-token: write`); no API token is stored.

### One-time trusted-publishing setup

On [pypi.org](https://pypi.org), for the `provenance-cli` project (or as a
pending publisher before the first release):

- **Your project → Publishing → Add a new pending publisher**
- Owner: `nndn`, Repository: `Provenance`, Workflow: `publish-pypi.yml`

## Manual publish

Build only:

```sh
sh scripts/build.sh        # rm -rf dist && uv build; lists artifacts
```

Build and publish with an API token
(create one at <https://pypi.org/manage/account/token/>):

```sh
UV_PUBLISH_TOKEN=pypi-... sh scripts/publish.sh
```

The script errors with instructions if `UV_PUBLISH_TOKEN` is unset.
Equivalent raw commands: `uv build && uv publish`.

## TestPyPI

To publish to TestPyPI instead, add an index to `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
```

then run `uv publish --index testpypi` with a TestPyPI token.
