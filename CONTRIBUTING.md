## Contribution Guide

### Dev Environment Setup

#### Docker Container

### Committing & Branching

#### Checking Out

Once your environment is setup, contributing to clpipe starts with checking out the
`develop` branch. This branch contains all of the progress of the next version of clpipe.
Its version will, naturally, be higher than that of the `main` branch.

`git checkout develop`

#### Creating a Feature Branch

Generally, however, you should not commit directly against this branch.
It's easier to pick and choose the right moment to include a particular change in develop
when these changes are isolated to their own branches - it also helps to avoid conflict
with other changes until it is necessary, and makes reverting during development simple.
Exceptions to this rule include updating the version, and other small, one-off changes.

Instead, you should checkout a new branch against `develop`, which is sometimes called
a **feature branch**, although it does not have to be a feature per se. Your branch should,
however, enscapsulate some single idea, such as fixing a bug, or updating how a
particular command works.

`git checkout -b my-feature`

#### Committing

Commits, like feature branches, should also encapsulate a single idea. Commits do not have
to be limited to a single file, as long as the changes can all be logically grouped together.
For example, if you update a utility function, and therefore must update all of the files
where the utility is called, those changed should all be committed together.

Commit messages should be descriptive enough to be helpful to another programmer reading
over them. However, they do not need to include file location information or other
details that are implied by the commit itself.

By Git convention, commit messages should also be in present tense, as if giving a
command - commit messages should describe how the codebase gets from one state to another.

`git commit -m "Modify function name to make its purpose more intuitive."`

#### Integrating Changes from the Develop Branch

If the `develop` branch is updated while working on your feature branch, and you would
like to include those changes in your branch, you should rebase your branch on `develop`.
This will keep your feature up-to-date in a cleaner fashion than merging.

`git rebase develop`

### Merging your Feature into Develop

Unless you are a core clpipe contributor, merging into `develop` from your feature 
should be done via a pull request on GitHub. This will allow core contributors to review
your changes before integration into develop.

You should first push your branch to Github:

`git push origin my-feature`

Next, open a new pull request, with `my-feature` merging into `develop`. Once the
PR is accepted, it will be merged into `develop`.


### Release Strategy

#### Versioning Scheme

clpipe follows the `x.y.z` versioning scheme, where x is a breaking update, y introduces
major features, and z indicates minor updates. Example: `1.7.2`

#### Release Branch

When enough changes to the `develop` branch have been made, they can be merged together into
the main branch as a **release**. In order to allow futher development on the `develop`
branch to continue, a new branch should be created off of `develop` that is specific to that release.
The release branch should be named after the version `develop` was on when the release
branch was created - for example, `release-1.7.3`, if `develop` was on version 1.7.3.

The release branch also must be tagged with its version name. This is because
GitHub Releases uses tags to map release notes with a particular commit in the
repository. The tag name should follow the scheme `v<x.y.z>`, which in our example
would be `v1.7.3`


#### Incrementing Develop

As soon as a release branch is created, the `develop` branch should have its version
updated in `setup.py`, usually by the minor value. For example, from `1.7.2` to `1.7.3`. If a major feature or breaking change
is included in subsequent development, the version should be updated to reflect this before release.

#### Release Branch PR to Main

#### Release Tagging, Documentation, and Artifact Distribution

#### Hotfixes

In general, releases are final and should not be updated. However, 
in the event that a bug is found in a release that cannot wait until the next release
for a fix, the release should be updated with a hotfix. 

Hotfixes become a "sub-version"
of the release, adding a fourth digit to the versioning scheme - now x.y.z.a, where
"a" is the hotfix. For example, the first hotfix off of clpipe version `1.7.3` would be 
version `1.7.3.1`. This digit is dropped in the next release - for example, a minor update
release from `1.7.3.1` would be named `1.7.4`. 

Changes for the hotfix should be made on a new branch created off the release branch. The
branch should be named with the scheme `x.y.z.a-HOTFIX`. For the hotfix in our previous examples,
the branch name would be `1.7.3.1-HOTFIX`. Upon creation of the branch, the version in
`setup.py` should be immediately changed to the hotfix verison and committed.

Once the hotfix changes are made and committed, a PR against the release branch is made
and merged once accepted. At the same time, a new tag should be created 
named after the hotfix, like `v1.7.3.1`. Once the tag is created, the GitHub documentation
for the release should be updated to point to this hotfixed version.

Finally, if the `x.y.z` version of main is the same as the release branch being
hotfixed, a PR should be made from the release branch to main to update
the main repository with the hotfix.

