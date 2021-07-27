# Dup-composer release workflow

## Branches

### Mainline (master)
Development for fixes and new features all happens in this branch. The aim is to always keep the mainline in a healthy state (tests passing) that is ready for release. Commits of partially developed features must not impact the mainline health. If a test is failing after a push to the mainline, it is of outmost priority to fix it and make the branch healthy again.

### Release (release)
Releases are created by merging the releasable HEAD from the mainline to this branch. Critical fixes for the last release are committed to this branch directly, then if the fix is also applicable to the mainline, they are picked for the mainline as well.

## A typical release workflow

### Initial state

Both the mainline and the release branch HEAD is at the latest release, no further commits occured on either branches.

### Development of new features or fixes begins

Work happens on the mainline and new code, along with code testing it are committed and pushed regularly on the mainline (master) branch, tests have to pass both before commits and automated tests after pushes. If the automated tests fail, making those pass to keep the mainline healthy is the top priority.

Pushing your commits to `origin/master` will trigger the test workflow in GitHub Actions.

### Making a development release

When making the first development release (PyPi package and OCI image), it has to be decided, if the current development cycle will:

- Contain simply fixes. (patch release)
- Contain new smaller features with no effect on backwards compatibility. (minor release)
- Contain larger features or features breaking backwards compatibility. (major release)

Depending on the choice, the new release has to be created with the release.py script with different parameters:

```shell
# Create a new patch development release chain
utils/release.py dev patch
# Create a new minor development release chain
utils/release.py dev minor
# Create a new major development release chain
utils/release.py dev major
```

The script will take care of the following:

- Pull changes from origin.
- Check if you have any uncommitted local changes, or if you are ahead of origin, if so, the release fails.
- Increment the package version string in `setup.py`.
- Commit and push the change to `master`.
- Merge the HEAD of `master` into the `release` branch.
- Tag the HEAD of the `release` branch according to the version to be released.
- Push the tag to origin.

Pushing the release tag will trigger the release worklow in GitHub Actions.

### Subsequent development releases

Once you have made the first development release for a patch, minor, major release, subsequent development releases can be done with the same workflow, but you have to simply run:

```shell
utils/release.py dev
```

This will only work, if you have already started a development release chain, otherwise it will fail.

### Releasing the new version

Once you are done with all the work and testing and you are ready to release the new version, you should run:

```shell
utils/release.py ga
```
