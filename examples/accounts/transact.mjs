#!/usr/bin/env node

/*
 * This is free and unencumbered software released into the public domain.
 *
 * Anyone is free to copy, modify, publish, use, compile, sell, or
 * distribute this software, either in source code form or as a compiled
 * binary, for any purpose, commercial or non-commercial, and by any
 * means.
 *
 * In jurisdictions that recognize copyright laws, the author or authors
 * of this software dedicate any and all copyright interest in the
 * software to the public domain. We make this dedication for the benefit
 * of the public at large and to the detriment of our heirs and
 * successors. We intend this dedication to be an overt act of
 * relinquishment in perpetuity of all present and future rights to this
 * software under copyright law.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
 * OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * For more information, please refer to <https://unlicense.org/>
 */

async function main() {
  const args = process.argv.slice(2);
  let account;
  let deposit;
  let withdraw;
  let verbose = false;
  let showJson = false;
  const positional = [];

  function valueFor(option, index) {
    const equalsIndex = option.indexOf("=");
    if (equalsIndex !== -1) {
      return [option.slice(equalsIndex + 1), index];
    }

    if (index + 1 >= args.length || args[index + 1].startsWith("-")) {
      throw new Error(`Missing value for ${option}`);
    }
    return [args[index + 1], index + 1];
  }

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "-v" || arg === "--verbose") {
      verbose = true;
    } else if (arg === "-j" || arg === "--json") {
      showJson = true;
    } else if (arg === "-a" || arg === "--account" || arg.startsWith("--account=")) {
      const [value, lastIndex] = valueFor(arg, i);
      account = value;
      i = lastIndex;
    } else if (arg === "-d" || arg === "--deposit" || arg.startsWith("--deposit=")) {
      const [value, lastIndex] = valueFor(arg, i);
      deposit = value;
      i = lastIndex;
    } else if (arg === "-w" || arg === "--withdraw" || arg.startsWith("--withdraw=")) {
      const [value, lastIndex] = valueFor(arg, i);
      withdraw = value;
      i = lastIndex;
    } else if (arg === "--") {
      positional.push(...args.slice(i + 1));
      break;
    } else if (arg.startsWith("-")) {
      throw new Error(`Unknown option: ${arg}`);
    } else {
      positional.push(arg);
    }
  }

  account ||= positional[0];

  if (!account) {
    console.error("Account number not provided");
    return 1;
  }

  if (deposit !== undefined && withdraw !== undefined) {
    console.error("Choose either --deposit or --withdraw, not both.");
    return 1;
  }

  let method = "GET";
  let route = `/api/accounts/${encodeURIComponent(account)}`;
  let amount;

  if (deposit !== undefined) {
    method = "POST";
    amount = deposit;
    route += "/deposits";
  } else if (withdraw !== undefined) {
    method = "POST";
    amount = withdraw;
    route += "/withdrawals";
  }

  const url = `http://localhost:8000${route}`;
  const options = { method, headers: {} };

  if (method === "POST") {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify({ amount });
  }

  if (verbose) {
    console.log(
      `curl -s -i -X ${method} ${url}` +
        (method === "POST"
          ? ` -H 'Content-Type: application/json' -d '${JSON.stringify({ amount })}'`
          : "")
    );
  }

  let response;
  let body;

  try {
    response = await fetch(url, options);
    body = await response.text();
  } catch (error) {
    console.error(`Request failed: ${error.message}`);
    return 1;
  }

  if (verbose) {
    console.log(`HTTP/${response.status} ${response.statusText}`);
    for (const [name, value] of response.headers) {
      console.log(`${name}: ${value}`);
    }
  }

  let result;
  try {
    result = JSON.parse(body);
  } catch {
    console.error(`Response was not valid JSON:\n${body}`);
    return 1;
  }

  if (showJson) {
    console.log(JSON.stringify(result, null, 2));
  }

  if (verbose || showJson) {
    console.log();
  }

  const accountData = result?.account;
  const balance = accountData?.balance;

  if (
    accountData?.account_number === undefined ||
    balance?.currency === undefined ||
    balance?.value === undefined
  ) {
    console.error("Response did not contain the expected account details.");
    return 1;
  }

  console.log("Account details\n---------------");
  console.log(`Account:\t${accountData.account_number}`);
  console.log(`Currency:\t${balance.currency}`);
  console.log(`Balance:\t${balance.value}`);

  return 0;
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
