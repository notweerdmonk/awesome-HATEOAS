# Hypermedia Demo - Accounts

A small Python 3 HTTP server demonstrating how a server can guide a client through an application by returning links and actions that depend on the current resource state.

The demo provides the same account workflow in two representations:

- **HTML:** a browser-oriented account page with links and forms.
- **JSON:** an API representation with links and action metadata.

The balance is held in memory and resets to `$100.00` when the server restarts. This is an educational example, not a production banking service.

## Run it

Save the server code as `server.py` and run:

```bash
python3 server.py
```

Open `http://localhost:8000/` for links to the HTML account and JSON API entry point.

**GET /api — API entry point**

```bash
curl -i http://localhost:8000/api
```

**GET /api/accounts/12345 — account representation and available actions**

```bash
curl -i http://localhost:8000/api/accounts/12345
```

**POST /api/accounts/12345/deposits — deposit $25.00**

```bash
curl -i -X POST http://localhost:8000/api/accounts/12345/deposits \
  -H 'Content-Type: application/json' \
  -d '{"amount": 25.00}'
```

**POST /api/accounts/12345/withdrawals — withdraw $10.00**

```bash
curl -i -X POST http://localhost:8000/api/accounts/12345/withdrawals \
  -H 'Content-Type: application/json' \
  -d '{"amount": 10.00}'
```

The POST commands return the updated account JSON. Each starts from whatever balance the running server currently has; restarting the server resets it to `$100.00`.

## Hypermedia and HATEOAS

HATEOAS stands for **Hypermedia as the Engine of Application State**. It is a REST architectural constraint: a client follows links and other controls provided in server responses to discover what it can do next. The server’s representation can change with application state—for example, an overdrawn account can offer a deposit action but omit withdrawals. <citation src="1"></citation>

The htmx essay explains this idea using HTML links and forms, and contrasts those with JSON representations. The Wikipedia article also illustrates HATEOAS with JSON links that vary according to account state. This demo follows both approaches: its HTML uses native links and forms, while its JSON response includes links and action descriptions. <citation src="4,1"></citation>

## HTML and JSON compared

| Aspect | HTML routes | JSON API |
|---|---|---|
| Intended client | A web browser | A program that understands this API’s JSON format |
| Navigation | HTML links such as `<a href="…">` | URLs in the `links` object |
| Submitting an action | A `<form>` specifies the method, destination, and input fields | An `actions` entry specifies the `href`, method, content type, and field name |
| State-dependent actions | The account page includes or omits action links | The account response includes or omits action links and actions |
| What the client needs to know | How to render and interact with standard HTML controls | How to interpret this API’s JSON shape and action semantics |

HTML forms carry interaction details in standard browser-understood elements. The JSON response in this demo adds method and field metadata to its links, making it more descriptive than a bare list of URLs. However, it uses a custom JSON shape; a client still needs to understand that format and the meaning of the actions. This reflects the distinction made in the htmx essay between HTML’s built-in hypermedia controls and JSON, where hypermedia conventions must be represented explicitly. <citation src="4"></citation>

## HTML routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Shows links to the HTML account and API entry point |
| `GET` | `/accounts/12345` | Displays the balance and currently available actions |
| `GET` | `/accounts/12345/deposits` | Displays the deposit form |
| `POST` | `/accounts/12345/deposits` | Submits a deposit |
| `GET` | `/accounts/12345/withdrawals` | Displays the withdrawal form, unless the balance is negative |
| `POST` | `/accounts/12345/withdrawals` | Submits a withdrawal, unless the balance is already negative |

The forms submit `amount` as `application/x-www-form-urlencoded`. A successful submission redirects to `/accounts/12345` with status `303 See Other`. The refreshed account page reflects the updated balance and available actions. Invalid amounts return `400`; a withdrawal when the balance is already negative returns `403`.

## JSON API routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api` | API entry point; links to the account |
| `GET` | `/api/accounts/12345` | Returns the account, its links, and available actions |
| `POST` | `/api/accounts/12345/deposits` | Adds funds to the account |
| `POST` | `/api/accounts/12345/withdrawals` | Subtracts funds, unless the balance is already negative |

The API returns `application/json`. For example, when the balance is not negative, `GET /api/accounts/12345` includes links and actions for both deposits and withdrawals. When it is negative, the withdrawal link and action are omitted.

An API deposit request can be sent as JSON:

```http
POST /api/accounts/12345/deposits
Content-Type: application/json

{"amount": 25.00}
```

A successful API action returns the updated account representation with status `200`. Amounts must be positive and have no more than two decimal places. The server also accepts form-encoded amounts on API POST routes, though the action metadata advertises JSON.

## Limitations

This server is for demonstration purposes:

- Account state is stored in a single in-memory variable; it is not persistent.
- There is no authentication, authorization, database, or concurrency protection.
- The JSON format and action metadata are custom, not a standardized hypermedia format.
- A withdrawal can make the balance negative; further withdrawals are then unavailable, while deposits remain available.

## References

[1]: <https://en.wikipedia.org/wiki/HATEOAS> "HATEOAS — Wikipedia"
[2]: <https://htmx.org/essays/hateoas/> "HATEOAS — htmx essay"
