#!/usr/bin/env bash

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

make_optstring() {
  [[ -z "$@" ]] && return 0

  short_opts=""
  long_opts=""
  
  IFS="," read -r -a args <<< "$@"
  for arg in "${args[@]}"
  do
    opt="${arg%%:*}"
    arg_required="${arg##*:}"
    [[ "$arg_required" == "arg" || -n "$arg_required" ]] && \
      arg_required=1 || \
      arg_required=0

    [[ -n "$long_opts" ]] && long_opts+=","

    short_opts+="${opt:0:1}"
    long_opts+="${opt}"

    [[ $arg_required -ne 0 ]] && \
      {
        short_opts+=":"
        long_opts+=":"
      }
  done

  echo "-o $short_opts --long $long_opts"

}

optstring="$(make_optstring account:arg,deposit:arg,withdraw:arg,verbose:,json:)"

opts=$(getopt "$optstring" -n "$0" -- "$@")
if [[ $? -ne 0 ]]; then
  exit 1
fi
eval set -- "$opts"

verbose=0
show_json=0

amount=0.00
action="query"

while true; do
  case "$1" in
    -a|--account)
      account="$2"
      shift 2
      ;;
    -d|--deposit)
      amount="$2"
      action="deposit"
      shift 2
      ;;
    -w|--withdraw)
      amount="$2"
      action="withdraw"
      shift 2
      ;;
    -j|--json)
      show_json=1
      shift
      ;;
    -v|--verbose)
      verbose=1
      shift
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

[[ -z "$account" ]] && account="$@"

[[ -z "$account" ]] && echo "Account number not provided" && exit 1

hostaddr="http://localhost:8000"

request=""
route="/api/accounts/$account"

case "$action" in
  "query")
    request="GET"
    ;;
  "deposit")
    request="POST"
    route+="/deposits"
    ;;
  "withdraw")
    request="POST"
    route+="/withdrawals"
    ;;
  *)
    ;;
esac

url="$hostaddr$route"

declare -a curl_cmd
curl_cmd+=("curl")
curl_cmd+=("-s")
curl_cmd+=("-i")
curl_cmd+=("-X $request")
curl_cmd+=("$url")
[[ "$request" == "POST" ]] && \
  {
    curl_cmd+=(" -H 'Content-Type: application/json'")
    curl_cmd+=("-d '{\"amount\": $amount}'")
  }

[[ $verbose -ne 0 ]] && echo "${curl_cmd[*]}"

response="$(bash -c "${curl_cmd[*]}")"
header="${response%%$'\r\n\r\n'\{*}"
json="${response##*$'\r\n\r\n'}"

[[ $verbose -ne 0 ]] && echo "$header"

[[ $show_json -ne 0 ]] && echo "$json" | jq

[[ $verbose -ne 0 || $show_json -ne 0 ]] && echo


printf "Account details\n---------------\n"

jq_format='
  "Account:\t\(.account_number)\n" +
  "Currency:\t\(.balance.currency)\n" +
  "Balance:\t\(.balance.value)"
'

jq -r ".account | ($jq_format)" <<< "$json"
