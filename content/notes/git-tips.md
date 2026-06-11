---
title: 'Tips for using Git and GitHub'
date: 2021-01-25
---
## Storing credentials
A useful command for storing Git credentials (username and password) in memory for 15 minutes: 

```bash
git config --global credential.helper cache
```
or permanently in plaintext file `~/..git-credentials` (when using the `--global` flag)

```bash
git config --global credential.helper store
``` 
For additional info see [this post](https://stackoverflow.com/questions/5343068/is-there-a-way-to-cache-github-credentials-for-pushing-commits) or [this one](https://superuser.com/questions/199507/how-do-i-ensure-git-doesnt-ask-me-for-my-github-username-and-password).

To see which method of credential storage we are using, issue the command
```bash
git config -l
```

## GitHub Access token
Once a [personal GitHub access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) is created, it can be used in place of a password (together with the username) for command line operations such as `git push`.


DISCLAIMER: This guide is provided for **purely educational** purposes. I take no responsibility for any consequences the may result from following these instructions.
