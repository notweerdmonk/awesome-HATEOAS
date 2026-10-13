#!/usr/bin/env python3

# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <https://unlicense.org/>

# https://htmx.org/essays/hateoas/

from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlsplit

ACCOUNT = "12345"
BALANCE = Decimal("100.00")
CENT = Decimal("0.01")


class AccountHandler(BaseHTTPRequestHandler):
    def send_body(self, body, content_type, status=200, headers=None):
        body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200, headers=None):
        self.send_body(html, "text/html; charset=utf-8", status, headers)

    def send_json(self, data, status=200, headers=None):
        body = json.dumps(data, indent=2)
        self.send_body(body, "application/json; charset=utf-8", status, headers)

    def account_path(self, api=False):
        prefix = "/api" if api else ""
        return f"{prefix}/accounts/{ACCOUNT}"

    def account_json(self):
        account_url = self.account_path(api=True)
        links = {
            "self": account_url,
            "deposits": f"{account_url}/deposits",
        }
        actions = {
            "deposit": {
                "href": links["deposits"],
                "method": "POST",
                "content_type": "application/json",
                "fields": ["amount"],
            }
        }

        # Withdrawals are available only while the account is not overdrawn.
        if BALANCE >= 0:
            links["withdrawals"] = f"{account_url}/withdrawals"
            actions["withdrawal"] = {
                "href": links["withdrawals"],
                "method": "POST",
                "content_type": "application/json",
                "fields": ["amount"],
            }

        return {
            "account": {
                "account_number": int(ACCOUNT),
                "balance": {
                    "currency": "usd",
                    "value": float(BALANCE),
                },
                "links": links,
                "actions": actions,
            }
        }

    def account_html(self):
        account_url = self.account_path()
        links = [
            f'<li><a href="{account_url}/deposits">Deposits</a></li>'
        ]

        if BALANCE >= 0:
            links.append(
                f'<li><a href="{account_url}/withdrawals">Withdrawals</a></li>'
            )

        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Account {ACCOUNT}</title></head>
<body>
  <h1>Account {ACCOUNT}</h1>
  <p>Balance: ${BALANCE:,.2f} USD</p>
  <h2>Available actions</h2>
  <ul>{"".join(links)}</ul>
</body>
</html>"""

    def action_form(self, action):
        account_url = self.account_path()
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{action.title()}</title></head>
<body>
  <h1>{action.title()}</h1>
  <form method="post" action="{account_url}/{action}">
    <label>Amount (USD):
      <input name="amount" type="number" min="0.01" step="0.01" required>
    </label>
    <button type="submit">Submit</button>
  </form>
  <p><a href="{account_url}">Back to account</a></p>
</body>
</html>"""

    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/":
            self.send_html(
                '<p><a href="/accounts/12345">HTML account</a></p>'
                '<p><a href="/api">JSON API entry point</a></p>'
            )
        elif path == "/api":
            self.send_json({
                "links": {
                    "account": self.account_path(api=True),
                }
            })
        elif path == self.account_path(api=True):
            self.send_json(self.account_json())
        elif path == self.account_path():
            self.send_html(self.account_html())
        elif path == f"{self.account_path()}/deposits":
            self.send_html(self.action_form("deposits"))
        elif path == f"{self.account_path()}/withdrawals":
            if BALANCE < 0:
                self.send_html("<p>Withdrawal unavailable.</p>", status=403)
            else:
                self.send_html(self.action_form("withdrawals"))
        else:
            self.send_html("<h1>Not found</h1>", status=404)

    def read_amount(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        try:
            if "application/json" in content_type:
                data = json.loads(raw_body.decode("utf-8"))
                raw_amount = data["amount"]
            else:
                data = parse_qs(raw_body.decode("utf-8"))
                raw_amount = data.get("amount", [""])[0]

            amount = Decimal(str(raw_amount))
            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation
            if amount != amount.quantize(CENT):
                raise InvalidOperation
            return amount
        except (InvalidOperation, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def do_POST(self):
        global BALANCE

        path = urlsplit(self.path).path
        api = path.startswith("/api/")
        account_url = self.account_path(api=api)

        if path not in {
            f"{account_url}/deposits",
            f"{account_url}/withdrawals",
        }:
            self.send_json({"error": "Not found"}, status=404) if api else \
                self.send_html("<h1>Not found</h1>", status=404)
            return

        action = path.rsplit("/", 1)[-1]
        amount = self.read_amount()

        if amount is None:
            error = {"error": "amount must be a positive number with at most two decimal places"}
            if api:
                self.send_json(error, status=400)
            else:
                self.send_html(f"<p>{error['error']}</p>", status=400)
            return

        if action == "withdrawals" and BALANCE < 0:
            if api:
                self.send_json({"error": "Withdrawal unavailable"}, status=403)
            else:
                self.send_html("<p>Withdrawal unavailable.</p>", status=403)
            return

        if action == "deposits":
            BALANCE += amount
        else:
            BALANCE -= amount

        if api:
            self.send_json(self.account_json())
        else:
            self.send_response(303)
            self.send_header("Location", self.account_path())
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), AccountHandler)
    print("Serving http://localhost:8000/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.server_close()
