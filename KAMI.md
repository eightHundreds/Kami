# Kami build and updates

This repository is a personal build of [Mika](https://github.com/wangzan101/Mika). The app installed from Kami releases has application ID **com.eighthundreds.kami**, displays as **Kami**, and checks releases from this repository.

## Build and release

The **Kami release** workflow runs for pushes to **main** and can also be started from **Actions → Kami release → Run workflow**. Syncing the fork's main branch with upstream updates that branch; GitHub Actions runs the workflow for the resulting main-branch push.

The build applies the Kami identity in the Actions runner's temporary checkout. It changes the application ID, app label, in-app repository/update URLs, and release version for the generated APKs. This keeps those customizations out of upstream source files, reducing sync conflicts. Internal Kotlin namespaces and source paths remain upstream-compatible.

Each run publishes two signed assets to a GitHub Release:

- **Kami-v<version>.apk**: universal APK
- **Kami-v<version>-arm64.apk**: smaller arm64 APK

The version includes the upstream version plus the GitHub Actions run number and attempt, so successive syncs remain detectable by the in-app updater even if upstream has not changed its version yet.

## Signing setup required

The workflow skips the build until these four repository Actions secrets exist:

- **KAMI_SIGNING_KEYSTORE_BASE64**: base64-encoded Android signing keystore
- **KAMI_SIGNING_STORE_PASSWORD**: keystore password
- **KAMI_SIGNING_KEY_ALIAS**: key alias
- **KAMI_SIGNING_KEY_PASSWORD**: key password

The same signing key must be used for every Kami release. The app verifies the APK signer before installation, so replacing the key would prevent in-app updates. Because the application ID differs from Mika, the first Kami install is a separate app installation; later Kami releases can update it.

After configuring the secrets, use **Actions → Kami release → Run workflow** for the first release. Subsequent pushes or upstream syncs to main publish automatically.
