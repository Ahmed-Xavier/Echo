# Local operator notes

This file intentionally contains no credentials, private network addresses, usernames,
or machine-specific filesystem paths. Keep deployment-specific values outside Git.

## GitHub

- Repository: <https://github.com/Ahmed-Xavier/Echo>
- Use the GitHub CLI or an SSH credential configured on the operator workstation.
- Never store access tokens in Git remotes, documentation, scripts, or `.env.example` files.

## Runtime configuration

Copy the relevant example environment file to a local, ignored environment file and
provide values on the robot:

- `runtime/voice/.env.example`
- `runtime/bin/echo_env.sh`

The canonical ROS 2 source tree is `src/`, built from the repository root. Paths
to the workspace, device ports, and runtime directories should be supplied through environment variables
or launch arguments rather than committed machine-specific values.
