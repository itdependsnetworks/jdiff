# netcompare

netcompare is a python library targeted at intelligently deep diffing structured data objects of different types. In addition, netcompare provides some basic tests of keys and values within the data structure. Ultimately, this library is meant to be a light-weight way to compare structured output from network device 'show' commands. 

## Use Case

netcompare enables an easy and direct way to see the outcome of network change windows. The intended usage is to collect raw show command output before and after a change window. Prior to closing the change window, the results are compared to help determine if the change was successful and if the network is in an acceptable state. The output can be stored with the change's documentation for easy reference and proof of completion.

## Check Types

### exact_match

exact_match is concerned about the value of the elements within the data structure. The keys and values should match between the pre and post values.

```
PASS 
--------------------
pre: [{"A": 1}]
post: [{"A": 1}]
```

```
FAIL
--------------------
pre: [{"A": 1}]
post: [{"A": 2}]
```

```
FAIL
--------------------
pre: [{ "A": 1}]
post: []
```

### parameter_match

parameter_match provides a way to match keys and values in the output with known good values. 

The test defines key/value pairs known to be the good value - type `dict()` - to match against the parsed output. The test FAILS if any status has changed based on what is defined in pre/post. If there are new values not contained in the input/test value, that will not count as a failure.


Examples:

```
{"A": 1, "B": 2}

PASS/PASS
{"A": 1, "B": 2}
{"A": 1, "B": 2}

PASS/PASS
{"A": 1, "B": 2}
{"A": 1, "B": 2, "C": 3}

PASS/FAIL
{"A": 1, "B": 2}
{"A": 1, "B": 666}

FAIL/PASS
{"A": 1}
{"A": 1, "B": 2}
```

In network data, this could be a state of bgp neighbors being Established or the connectedness of certain interfaces being up.

### Tolerance

The `tolerance` test defines a percentage of differing `float()` between the pre and post checks. The threshold is defined as a percentage that can be different either from the value stated in pre and post fields. 

The threshold must be `float > 0`, is percentge based, and will be counted as a range centered on the value in pre and post.

```
Pre: 100 
Post: 110
Threshold: 10
-----------------
PASS/PASS
Pre:  [100]
Post: [110]

PASS/PASS
Pre:  [100]
Post: [120]

PASS/PASS
Pre:  [100]
Post: [100]

PASS/FAIL
Pre:  [100]
Post: [90]

PASS/FAIL
Pre:  [90]
Post: [20]

FAIL/FAIL
Pre:  [80]
Post: [120]
```

This test can test the tolerance for changing quantities of certain things such as routes, or L2 or L3 neighbors. It could also test actual outputted values such as transmitted light levels for optics.

## How To Define A Check

The check requires at least 2 arguments: `check_type` which can be `exact_match`, `tolerance`, `parameter_match` or `path`. The `path` argument is JMESPath based but uses `$` to anchor the reference key needed to generate the diff - more on this later. 

Example #1:

Run an `exact_match` between 2 files where `peerAddress` is the reference key (note the anchors used - `$` ) for `statebgpPeerCaps`. In this example, key and value are at the same level.

Check Definition:
```
{
  "check_type": "exact_match",
  "path": "result[0].vrfs.default.peerList[*].[$peerAddress$,statebgpPeerCaps]",
}
```

Show Command Output - Pre:
```
{
  "jsonrpc": "2.0",
  "id": "EapiExplorer-1",
  "result": [
    {
      "vrfs": {
        "default": {
          "peerList": [
            {
              "linkType": "external",
              "localAsn": "65130.1100",
              "prefixesSent": 52,
              "receivedUpdates": 0,
              "peerAddress": "7.7.7.7",
              "v6PrefixesSent": 0,
              "establishedTransitions": 0,
              "bgpPeerCaps": 75759616,
              "negotiatedVersion": 0,
              "sentUpdates": 0,
              "v4SrTePrefixesSent": 0,
              "lastEvent": "NoEvent",
              "configuredKeepaliveTime": 5,
              "ttl": 2,
              "state": "Idle",
              ...
```
Show Command Output - Post:
```
{
  "jsonrpc": "2.0",
  "id": "EapiExplorer-1",
  "result": [
    {
      "vrfs": {
        "default": {
          "peerList": [
            {
              "linkType": "external",
              "localAsn": "65130.1100",
              "prefixesSent": 50,
              "receivedUpdates": 0,
              "peerAddress": "7.7.7.7",
              "v6PrefixesSent": 0,
              "establishedTransitions": 0,
              "bgpPeerCaps": 75759616,
              "negotiatedVersion": 0,
              "sentUpdates": 0,
              "v4SrTePrefixesSent": 0,
              "lastEvent": "NoEvent",
              "configuredKeepaliveTime": 5,
              "ttl": 2,
              "state": "Connected",
```

Result:
```
{
    "7.7.7.7": {
        "state": {
            "new_value": "Connected",
            "old_value": "Idle"
        }
    }
}
```
`result[0].vrfs.default.peerList[*].$peerAddress$` is the reference key (`7.7.7.7`) that we want associated to our value used to generate diff (`state`)...otherwise, how can we understand which `statebgpPeerCaps` is associated to which `peerAddress` ?

Example #2:

Similar to Example 1 but with key and value on different level. In this example `peers` will be our reference key, `accepted_prefixes` and `received_prefixes` the values used to generate diff.

Check Definition:
```
{
  "check_type": "exact_match",
  "path": "global.$peers$.*.*.ipv4.[accepted_prefixes,received_prefixes]",
}
```

Show Command Output - Pre:
```
{
    "global": {
        "peers": {
            "10.1.0.0": {
                "address_family": {
                    "ipv4": {
                        "accepted_prefixes": -9,
                        "received_prefixes": 0,
                        "sent_prefixes": 0
                    },
                    ....
```

Show Command Output - Post:
```
{
    "global": {
        "peers": {
            "10.1.0.0": {
                "address_family": {
                    "ipv4": {
                        "accepted_prefixes": -1,
                        "received_prefixes": 0,
                        "sent_prefixes": 0
                        ...
```

Result:
```
{
    "10.1.0.0": {
        "accepted_prefixes": {
            "new_value": -1,
            "old_value": -9
        }
    },
    ...
```

Example #3:

Similar to Example 1 and 2 but without a reference key defined in `path`, plus some excluded fields to remove verbosity from diff output

Check Definition:
```
{
  "check_type": "exact_match", 
  "path": "result[*]", 
  "exclude": ["interfaceStatistics", "interfaceCounters"],
}
```

Show Command Output - Pre:
```
{
    "jsonrpc": "2.0",
    "id": "EapiExplorer-1",
    "result": [
      {
        "interfaces": {
          "Management1": {
            "lastStatusChangeTimestamp": 1626247820.0720868,
            "lanes": 0,
            "name": "Management1",
            "interfaceStatus": "connected",
            "autoNegotiate": "success",
            "burnedInAddress": "08:00:27:e6:b2:f8",
            "loopbackMode": "loopbackNone",
            "interfaceStatistics": {
              "inBitsRate": 3582.5323982177174,
              "inPktsRate": 3.972702352461616,
              "outBitsRate": 17327.65267220522,
              "updateInterval": 300,
              "outPktsRate": 2.216220664406746
            },
            ...
```

Show Command Output - Post:
```
{
    "jsonrpc": "2.0",
    "id": "EapiExplorer-1",
    "result": [
      {
        "interfaces": {
          "Management1": {
            "lastStatusChangeTimestamp": 1626247821.123456,
            "lanes": 0,
            "name": "Management1",
            "interfaceStatus": "connected",
            "autoNegotiate": "success",
            "burnedInAddress": "08:00:27:e6:b2:f8",
            "loopbackMode": "loopbackNone",
            "interfaceStatistics": {
              "inBitsRate": 3403.4362520883615,
              "inPktsRate": 3.7424095978179257,
              "outBitsRate": 16249.69114419833,
              "updateInterval": 300,
              "outPktsRate": 2.1111866059750692
            },
          ...
```

Result:

```
{
  "interfaces": {
      "Management1": {
          "lastStatusChangeTimestamp": {
              "new_value": 1626247821.123456,
              "old_value": 1626247820.0720868
          },
          "interfaceAddress": {
              "primaryIp": {
                  "address": {
                      "new_value": "10.2.2.15",
                      "old_value": "10.0.2.15"
                  }
              }
          }
      }
  }
}
```

See [test](./tests) folder for more examples.

