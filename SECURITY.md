# Security Policy

This is a personal collection of custom Checkov checks, not intended for production use beyond this account's own repositories. There are no supported version branches — only `main` is maintained.

## Reporting a Vulnerability

If you find a security issue — an exposed secret, a leaked credential in git history, or a misconfigured workflow — please report it privately using [GitHub's private vulnerability reporting](../../security/advisories/new) instead of opening a public issue.

## Scope

- The Python checks in `custom_policies/aws/` and `custom_policies/azure/`
- `.github/workflows/`

Out of scope: vulnerabilities in [Checkov](https://github.com/bridgecrewio/checkov) itself — please report those to its maintainers.

## A note on running arbitrary Python

Checkov's `--external-checks-dir` loads and executes whatever `.py` files it finds as Python code. Consuming repos should only point this at a commit SHA they've reviewed, same as pinning any other action — never a floating branch ref.
