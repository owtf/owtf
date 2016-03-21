# Contributing to OWASP OWTF

Looking to contribute something to OWTF? **Here's how you can help.**

Please take a moment to review this document in order to make the contribution process easy
and effective for everyone involved. These are just guidelines, not rules, use your
best judgment and feel free to propose changes to this document in a pull request.

Following these guidelines helps to communicate that you respect the time of the developers
managing and developing this open source project. In return, they should reciprocate that
respect in addressing your issue or assessing patches and features.

For more detailed information, visit [OWTF wiki](https://github.com/owtf/owtf/wiki) or
[user documentation](http://docs.owtf.org/en/latest/).

#### Table Of Contents

[How Can I Contribute?](#how-can-i-contribute)
  * [Using the issue tracker](#using-the-issue-tracker)
  * [Your First Code Contribution](#your-first-code-contribution)
  * [Pull Requests](#pull-requests)

[Styleguides](#styleguides)
  * [Git Commit Messages](#git-commit-messages)
  * [Python Styleguide](#coffeescript-styleguide)
  * [Documentation Styleguide](#documentation-styleguide)


## How Can I Contribute?

### Using the issue tracker

The [issue tracker](https://github.com/owtf/owtf/issues) is the preferred channel for bug reports, features requests
and submitting pull requests, but please respect the following restrictions:

* Please **do not** use the issue tracker for personal support requests if possible.
  [IRC](http://webchat.freenode.net/?randomnick=1&channels=%23owtf&prompt=1&uio=MTE9MjM20f) and email
  are better places to get help.

* Please **do not** derail or troll issues. Keep the discussion on topic and respect the opinions of others.

* Please **do not** post comments consisting solely of "+1" or ":thumbsup:".
  Use [GitHub's "reactions" feature](https://github.com/blog/2119-add-reactions-to-pull-requests-issues-and-comments)
  instead. We reserve the right to delete comments which violate this rule.

* Please **do not** open issues or pull requests regarding the code of other repositories in
  [OWTF organisation](https://github.com/owtf) (open them in their respective repositories).

* Please perform **a cursory search** to see if the problem has already been reported. If it has, add a comment to the
  existing issue instead of opening a new one.


### Your First Code Contribution

Unsure where to begin contributing to OWTF? You can start by looking through these `beginner`, `easy-fix` and
`help-wanted` issues:

Both issue lists are sorted by total number of comments. While not perfect, number of comments is a reasonable
proxy for impact a given change will have.

### Pull Requests

* Include screenshots in your pull request whenever possible.
* Follow the [Python](#python-styleguide).
* Follow the pull request template provided.
* Document new code based on the [Documentation Styleguide](#documentation-styleguide)
* End files with a newline.
* Avoid platform-dependent code such as:
    * Use `os.path.join()` to concatenate filenames.
    * Use `tempfile.gettempdir()` rather than `/tmp/` when you need to reference the temporary directory.


## Styleguides

### Git Commit Messages

* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally

### Python Styleguide

### Documentation Styleguide
