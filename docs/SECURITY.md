# Echo security

## Credential handling

Credentials are supplied at runtime through environment variables. The tracked
examples contain names only:

- `PICOVOICE_ACCESS_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `ECHO_KEYWORD_PATH`
- `TELEGRAM_ID`

Copy `echo_runtime/voice/.env.example` to a local ignored file or export the values
through the robot's service manager. Never commit `.env`, voice environment files,
tokens, private keys, or local service configuration.

## Exposure assessment

The original repository snapshot contained live-looking Picovoice and ElevenLabs
credentials in scripts and runtime environment files, plus credential-related
documentation. Backup copies duplicated some of those values. This branch removes
the tracked values from retained source files and removes the backup/environment
artifacts from the working tree, but the values remain in earlier Git commits.

Because Git history is not rewritten here, assume the exposed credentials are
compromised and rotate or revoke them before merging or publishing this branch.

## Rotation checklist

1. Revoke and reissue the Picovoice access key.
2. Revoke and reissue the ElevenLabs API key.
3. Review any tokens or credentials referenced by `openclaw.json`, service overrides,
   or local deployment files and rotate them if they were ever committed.
4. Review GitHub token configuration separately; use GitHub credential storage or
   GitHub CLI authentication, never a remote URL or documentation entry.
5. Redeploy local environment files and restart affected services.
6. Review repository access logs after rotation.

Do not paste credential values into issues, pull requests, logs, or chat.
