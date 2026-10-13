---
layout: default
title: Awesome HATEOAS
permalink: /
---

# Awesome HATEOAS

Demonstrations, libraries, and learning resources for **HATEOAS** (Hypermedia as the Engine of Application State) and hypermedia-driven APIs.

HATEOAS is a REST constraint in which API responses provide links or controls that help clients discover available actions, rather than requiring clients to construct every URL themselves.

## Contents

- [Example: Accounts](#example-accounts)

## Example: Accounts

**[</> htmx ~ HATEOAS](https://htmx.org/essays/hateoas/)**

The [`examples/accounts/`](examples/accounts/) directory contains command-line clients for an accounts API. The clients can query an account, deposit funds, or withdraw funds. They expect the API server to be running at `http://localhost:8000`.

- [Bash client]({{ '/examples/accounts/account.sh' | relative_url }})
- [Python 3 client]({{ '/examples/accounts/account.py' | relative_url }})
- [Node.js client]({{ '/examples/accounts/account.mjs' | relative_url }})
- [Browse all account examples]({{ '/examples/accounts/' | relative_url }})
- [Accounts example readme]({{ 'examples/accounts/README.md' | relative_url }})

Example commands:

```bash
./examples/accounts/account.sh --account 123 --deposit 25.00
```

```bash
python3 examples/accounts/account.py --account 123 --json
```

```bash
node examples/accounts/account.mjs --account 123 --withdraw 5.00 --verbose
```
