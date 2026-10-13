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

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(
        description="Query an account, make a deposit, or make a withdrawal."
    )
    parser.add_argument("-a", "--account", help="account number")
    parser.add_argument("-d", "--deposit", metavar="AMOUNT", help="deposit amount")
    parser.add_argument("-w", "--withdraw", metavar="AMOUNT", help="withdrawal amount")
    parser.add_argument("-v", "--verbose", action="store_true", help="show request and response headers")
    parser.add_argument("-j", "--json", dest="show_json", action="store_true", help="print the raw JSON response")
    parser.add_argument("account_pos", nargs="?", help="account number (alternative to --account)")
    args = parser.parse_args()

    account = args.account or args.account_pos
    if not account:
        print("Account number not provided", file=sys.stderr)
        return 1

    if args.deposit is not None and args.withdraw is not None:
        parser.error("choose either --deposit or --withdraw, not both")

    action = "query"
    method = "GET"
    route = f"/api/accounts/{quote(account, safe='')}"

    amount = args.deposit if args.deposit is not None else args.withdraw
    if args.deposit is not None:
        action = "deposit"
        route += "/deposits"
    elif args.withdraw is not None:
        action = "withdraw"
        route += "/withdrawals"

    url = f"http://localhost:8000{route}"
    data = None
    headers = {}

    if action != "query":
        method = "POST"
        headers["Content-Type"] = "application/json"
        data = json.dumps({"amount": amount}).encode("utf-8")

    if args.verbose:
        print(f"curl -s -i -X {method} {url}" +
              (f" -H 'Content-Type: application/json' -d '{json.dumps({'amount': amount})}'"
               if data is not None else ""))

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(request) as response:
            body = response.read().decode("utf-8")
            response_headers = (
                f"HTTP/{response.version // 10}.{response.version % 10} "
                f"{response.status} {response.reason}\n{response.headers}"
            )
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        response_headers = (
            f"HTTP error {error.code} {error.reason}\n{error.headers}"
        )
    except URLError as error:
        print(f"Request failed: {error.reason}", file=sys.stderr)
        return 1

    if args.verbose:
        print(response_headers)

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(f"Response was not valid JSON:\n{body}", file=sys.stderr)
        return 1

    if args.show_json:
        print(json.dumps(result, indent=2))

    if args.verbose or args.show_json:
        print()

    try:
        account_data = result["account"]
        print("Account details\n---------------")
        print(f"Account:\t{account_data['account_number']}")
        print(f"Currency:\t{account_data['balance']['currency']}")
        print(f"Balance:\t{account_data['balance']['value']}")
    except (KeyError, TypeError):
        print("Response did not contain the expected account details.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
