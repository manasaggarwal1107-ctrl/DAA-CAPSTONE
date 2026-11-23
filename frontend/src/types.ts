// Shapes of the JSON exchanged with the backend (see backend/app/models.py and services/pipeline.py).

export type Status = 'pending' | 'delivered' | 'cancelled';

export interface Parcel {
  id: string;
  destination: string;
  weight: number;
  priority: number;
  deadline: string;
  value: number;
  status: Status;
}

export interface Location { name: string; x: number; y: number }
export interface Road { a: string; b: string; weight: number; bidirectional: boolean }
export interface GraphData { locations: Location[]; roads: Road[] }
export interface GraphWithAdjacency extends GraphData { adjacency: Record<string, { to: string; weight: number }[]> }

export interface Settings {
  capacity: number;
  depot: string;
  dispatch_time: string;
  speed_kmph: number;
  service_minutes: number;
}

export interface AppState { parcels: Parcel[]; graph: GraphData; settings: Settings }

export interface Leg { from: string; to: string; distance: number; path: string[]; cumulative: number }

export interface Delivery {
  destination: string;
  parcels: string[];
  weight: number;
  value: number;
  cumulative_km: number;
  eta: string;
  late: string[];
}

export interface RejectedParcel extends Parcel { reason: string }

export interface DpInfo {
  cells: number;
  table: number[][] | null;
  table_note: string;
  order: string[];
  weights: number[];
  values: number[];
}

export interface RouteInfo {
  depot: string;
  order: string[];
  legs: Leg[];
  return_leg: Leg | null;
  returned_to_depot: boolean;
  total_distance: number;
  dijkstra_runs: number;
  deliveries: Delivery[];
  on_time: number;
  late: number;
  note: string;
}

export interface Result {
  status: 'optimised' | 'partial_route' | 'nothing_selected' | 'nothing_deliverable' | 'no_parcels';
  ran_at: string;
  stale?: boolean;
  capacity: number;
  depot: string;
  original_order: string[];
  sorted_parcels: Parcel[];
  sort_comparisons: number;
  selected: Parcel[];
  rejected: RejectedParcel[];
  undeliverable: RejectedParcel[];
  counts: { pending: number; deliverable: number; selected: number; rejected: number; undeliverable: number; replans: number };
  used_weight: number;
  remaining_capacity: number;
  utilisation: number;
  total_value: number;
  raw_value: number;
  dp: DpInfo;
  destinations: string[];
  unreachable: string[];
  route: RouteInfo;
  timings_ms: Record<string, number>;
  warnings: string[];
}

export interface StageTiming { median_ms: number; min_ms: number; mean_ms: number; repeats: number; peak_kb: number }
export interface BenchmarkRow {
  n: number; locations: number; roads: number; capacity: number; selected: number; stops: number; dp_cells: number;
  sorting: StageTiming; knapsack: StageTiming; dijkstra: StageTiming; routing: StageTiming;
}
export interface Benchmark {
  generated_at: string;
  parameters: { sizes: number[]; repeats: number; seed: number; dp_capacity_cap_kg: number; capacity_rule: string; locations_rule: string };
  environment: { python: string; platform: string; processor: string };
  theory: Record<string, string>;
  rows: BenchmarkRow[];
  note: string;
}

export interface Dashboard {
  total_parcels: number;
  pending_parcels: number;
  locations: number;
  roads: number;
  priority_distribution: { priority: string; count: number }[];
  weight_distribution: { label: string; count: number }[];
  result: null | {
    status: Result['status']; ran_at: string; stale: boolean; selected: number; utilisation: number; capacity: number;
    used_weight: number; total_value: number; route_distance: number; timings_ms: Record<string, number>;
    deliveries: Delivery[]; on_time: number; late: number; warnings: string[];
  };
  benchmark: null | { generated_at: string; rows: BenchmarkRow[] };
}

export interface SortResponse {
  sorter: string; original: Parcel[]; sorted: Parcel[]; n: number; time_ms: number; repeats: number;
  comparisons: number; trace: MergeEvent[]; trace_parcels: string[]; complexity: { time: string; space: string };
}

export interface MergeEvent {
  type: 'split' | 'merge';
  depth: number;
  items?: (string | number)[];
  left: (string | number)[];
  right: (string | number)[];
  result?: (string | number)[];
}

export interface PathResponse {
  reachable: boolean; path: string[]; distance: number | null; message?: string;
  hops?: { from: string; to: string; distance: number }[];
}

export interface ImportResponse { added: number; total: number; errors: { row: number; field: string; message: string }[] }

export interface LearnAlgo {
  id: string; name: string; phase: string; role: string; concept: string; principle: string[];
  pseudocode: string; recurrence: string; time: { best: string; average: string; worst: string };
  space: string; notes: string[]; viva: { q: string; a: string }[];
}

export interface KnapsackDemo {
  weights: number[]; values: number[]; capacity: number; best_value: number; selected: number[];
  total_weight: number; table: number[][] | null;
}

export interface DijkstraStep {
  visit: string; distance: number; settled: string[]; distances: Record<string, number>;
  relaxed: { to: string; candidate: number; previous: number | null; improved: boolean }[];
}
export interface DemoGraph { locations: Location[]; roads: { a: string; b: string; weight: number }[] }
export interface DijkstraDemo extends DemoGraph { steps: DijkstraStep[]; path: string[] | null; distance: number | null }
export interface NnStep { from: string; candidates: { stop: string; distance: number }[]; unreachable: string[]; chosen: string | null }
export interface NnDemo extends DemoGraph {
  steps: NnStep[]; order: string[]; total_distance: number;
  legs: { from: string; to: string; distance: number; path: string[] }[];
  return_leg: { from: string; to: string; distance: number; path: string[] } | null;
}
export interface MergeDemo { input: number[]; output: number[]; steps: MergeEvent[]; comparisons: number }
