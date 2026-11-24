# Algorithm Execution Traces

## Evidence methodology

This document records actual outputs produced by the project's implemented
algorithms. The examples use small, controlled inputs so intermediate
operations can be inspected.

These are execution demonstrations, not performance measurements.
The benchmark measurements are documented separately in `BENCHMARKS.md`.

---

## 1. Merge Sort

**Input:** `[38, 12, 27, 43, 9, 31, 18]`

**Operation:** Ascending Merge Sort.

**Actual sorted output:** `[9, 12, 18, 27, 31, 38, 43]`

**Actual comparison count:** `14`

### Recorded split and merge events

```json
[
  {
    "type": "split",
    "depth": 0,
    "items": [
      38,
      12,
      27,
      43,
      9,
      31,
      18
    ],
    "left": [
      38,
      12,
      27
    ],
    "right": [
      43,
      9,
      31,
      18
    ]
  },
  {
    "type": "split",
    "depth": 1,
    "items": [
      38,
      12,
      27
    ],
    "left": [
      38
    ],
    "right": [
      12,
      27
    ]
  },
  {
    "type": "split",
    "depth": 2,
    "items": [
      12,
      27
    ],
    "left": [
      12
    ],
    "right": [
      27
    ]
  },
  {
    "type": "merge",
    "depth": 2,
    "left": [
      12
    ],
    "right": [
      27
    ],
    "result": [
      12,
      27
    ]
  },
  {
    "type": "merge",
    "depth": 1,
    "left": [
      38
    ],
    "right": [
      12,
      27
    ],
    "result": [
      12,
      27,
      38
    ]
  },
  {
    "type": "split",
    "depth": 1,
    "items": [
      43,
      9,
      31,
      18
    ],
    "left": [
      43,
      9
    ],
    "right": [
      31,
      18
    ]
  },
  {
    "type": "split",
    "depth": 2,
    "items": [
      43,
      9
    ],
    "left": [
      43
    ],
    "right": [
      9
    ]
  },
  {
    "type": "merge",
    "depth": 2,
    "left": [
      43
    ],
    "right": [
      9
    ],
    "result": [
      9,
      43
    ]
  },
  {
    "type": "split",
    "depth": 2,
    "items": [
      31,
      18
    ],
    "left": [
      31
    ],
    "right": [
      18
    ]
  },
  {
    "type": "merge",
    "depth": 2,
    "left": [
      31
    ],
    "right": [
      18
    ],
    "result": [
      18,
      31
    ]
  },
  {
    "type": "merge",
    "depth": 1,
    "left": [
      9,
      43
    ],
    "right": [
      18,
      31
    ],
    "result": [
      9,
      18,
      31,
      43
    ]
  },
  {
    "type": "merge",
    "depth": 0,
    "left": [
      12,
      27,
      38
    ],
    "right": [
      9,
      18,
      31,
      43
    ],
    "result": [
      9,
      12,
      18,
      27,
      31,
      38,
      43
    ]
  }
]
```

**Observation:** The algorithm recursively divides the input into smaller
subarrays and merges them in ascending order. The original input remains
unchanged.

---

## 2. 0/1 Knapsack Dynamic Programming

**Weights:** `[2, 3, 4, 5]`

**Values:** `[3, 4, 5, 8]`

**Vehicle capacity:** `8`

**Actual optimal value:** `12`

**Selected item indices (zero-based):** `[1, 3]`

**Selected weights:** `[3, 5]`

**Selected values:** `[4, 8]`

**Total selected weight:** `8`

**DP decision cells:** `36`

### Actual DP table

Rows represent the number of items considered, and columns represent
available capacity from 0 to 8.

```json
[
  [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    3,
    3,
    3,
    3,
    3,
    3,
    3
  ],
  [
    0,
    0,
    3,
    4,
    4,
    7,
    7,
    7,
    7
  ],
  [
    0,
    0,
    3,
    4,
    5,
    7,
    8,
    9,
    9
  ],
  [
    0,
    0,
    3,
    4,
    5,
    8,
    8,
    11,
    12
  ]
]
```

**Observation:** Each item can be selected at most once. The algorithm
uses descending capacity updates to implement the 0/1 constraint.

---

## 3. Dijkstra's Shortest Path Algorithm

### Demonstration road network

| From | To | Distance |
|---|---|---:|
| Depot | A | 4 |
| Depot | B | 2 |
| A | B | 1 |
| A | C | 5 |
| B | C | 8 |

All roads in this demonstration are bidirectional.

**Source:** Depot

### Actual shortest distances

```json
{
  "Depot": 0.0,
  "A": 3.0,
  "B": 2.0,
  "C": 8.0
}
```

**Actual shortest path from Depot to C:**
`['Depot', 'B', 'A', 'C']`

### Actual execution trace

```json
[
  {
    "visit": "Depot",
    "distance": 0.0,
    "relaxed": [
      {
        "to": "A",
        "candidate": 4.0,
        "previous": null,
        "improved": true
      },
      {
        "to": "B",
        "candidate": 2.0,
        "previous": null,
        "improved": true
      }
    ],
    "distances": {
      "Depot": 0.0,
      "A": 4.0,
      "B": 2.0
    },
    "settled": [
      "Depot"
    ]
  },
  {
    "visit": "B",
    "distance": 2.0,
    "relaxed": [
      {
        "to": "A",
        "candidate": 3.0,
        "previous": 4.0,
        "improved": true
      },
      {
        "to": "C",
        "candidate": 10.0,
        "previous": null,
        "improved": true
      }
    ],
    "distances": {
      "Depot": 0.0,
      "A": 3.0,
      "B": 2.0,
      "C": 10.0
    },
    "settled": [
      "B",
      "Depot"
    ]
  },
  {
    "visit": "A",
    "distance": 3.0,
    "relaxed": [
      {
        "to": "C",
        "candidate": 8.0,
        "previous": 10.0,
        "improved": true
      }
    ],
    "distances": {
      "Depot": 0.0,
      "A": 3.0,
      "B": 2.0,
      "C": 8.0
    },
    "settled": [
      "A",
      "B",
      "Depot"
    ]
  },
  {
    "visit": "C",
    "distance": 8.0,
    "relaxed": [],
    "distances": {
      "Depot": 0.0,
      "A": 3.0,
      "B": 2.0,
      "C": 8.0
    },
    "settled": [
      "A",
      "B",
      "C",
      "Depot"
    ]
  }
]
```

**Observation:** Dijkstra repeatedly settles the currently closest
unvisited vertex and relaxes its outgoing edges. The trace records
the distance updates and settled vertices.

---

## 4. Nearest Neighbour Route Heuristic

**Depot:** Depot

**Requested delivery stops:** `["A", "B", "C"]`

**Return to depot:** Enabled

### Actual candidate-selection trace

```json
[
  {
    "from": "Depot",
    "candidates": [
      {
        "stop": "B",
        "distance": 2.0
      },
      {
        "stop": "A",
        "distance": 3.0
      },
      {
        "stop": "C",
        "distance": 8.0
      }
    ],
    "unreachable": [],
    "chosen": "B"
  },
  {
    "from": "B",
    "candidates": [
      {
        "stop": "A",
        "distance": 1.0
      },
      {
        "stop": "C",
        "distance": 6.0
      }
    ],
    "unreachable": [],
    "chosen": "A"
  },
  {
    "from": "A",
    "candidates": [
      {
        "stop": "C",
        "distance": 5.0
      }
    ],
    "unreachable": [],
    "chosen": "C"
  }
]
```

### Actual route result

**Visit order:** `['B', 'A', 'C']`

**Returned to depot:** `True`

**Unreachable stops:** `[]`

**Dijkstra executions:** `4`

**Total route distance:** `16.0`

### Actual delivery legs

```json
[
  {
    "origin": "Depot",
    "destination": "B",
    "distance": 2.0,
    "path": [
      "Depot",
      "B"
    ]
  },
  {
    "origin": "B",
    "destination": "A",
    "distance": 1.0,
    "path": [
      "B",
      "A"
    ]
  },
  {
    "origin": "A",
    "destination": "C",
    "distance": 5.0,
    "path": [
      "A",
      "C"
    ]
  }
]
```

### Actual return leg

```json
{
  "origin": "C",
  "destination": "Depot",
  "distance": 8.0,
  "path": [
    "C",
    "A",
    "B",
    "Depot"
  ]
}
```

**Observation:** At each iteration, the heuristic chooses the nearest
reachable remaining stop using shortest-path distances. It is a heuristic
and does not guarantee a globally optimal travelling-salesperson tour.

---

## Reproducibility

The examples above are generated directly from the repository's
`merge_sort`, `knapsack_01`, `dijkstra`, and
`nearest_neighbour_route` functions.

No intermediate output in this document was manually fabricated.

To regenerate the evidence, execute the same algorithm calls using the
inputs documented in this file.
