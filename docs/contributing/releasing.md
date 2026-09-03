# Release OWTF

OWTF releases are created from a versioned commit on `develop`. A semantic version tag builds the Python source and wheel distributions, validates their metadata, creates checksums, and publishes a GitHub release.

## 1. Prepare the release commit

Update the same version in:

- `owtf/__init__.py`;
- the `current_version` value in `setup.cfg`;
- `CHANGELOG.md`; and
- `debian/changelog`.

Move the completed changes from **Unreleased** into a dated release section. Update `SECURITY.md` if the supported release line changes.

## 2. Validate locally

Install the isolated release dependencies and build the distributions:

```bash
python3 -m venv .venv-release
source .venv-release/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/release.txt
make release-check
```

Inspect both archives under `dist/`. Confirm that package metadata reports the intended version and that runtime dependencies do not include documentation or development tools.

Run the complete required CI suite on the release commit before tagging it.

## 3. Tag the verified commit

From an up-to-date, clean `develop` checkout:

```bash
git tag -a v2.7.0 -m "OWTF 2.7.0"
git push origin v2.7.0
```

The tag must exactly match the version in `owtf/__init__.py`. Pushing it triggers the **Publish Release** workflow, which creates the GitHub release and attaches the distributions and `SHA256SUMS` file.

## 4. Verify publication

After the workflow succeeds:

1. download the release assets and verify their checksums;
2. install the wheel in a clean Python 3.11 or 3.12 environment;
3. run the Compose quick start from a fresh clone;
4. confirm the GitHub release notes match `CHANGELOG.md`; and
5. update the documentation banner and project website to point at the new latest release.

Do not move or recreate a published tag. Correct release metadata with a new patch version.
