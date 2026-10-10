#!/usr/bin/env python3
"""Unified reproducibility checker for the U2 kernel constructive-expansion paper.

Runs the four supplied verification suites in their original order and writes:
  u2_finite_certificates.json
  marked_construction_certificates.json
  revised_sections_7_9_certificates.json
  infinite_transfer_certificates.json

Requires Python >= 3.10 and networkx (the paper specifies networkx==3.6.1).
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, permutations, product
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple
import networkx as nx
HERE = Path(__file__).resolve().parent
OUTPUT_DIR: Path | None = None
'===== KERNEL CHECKS ====='
Edge = Tuple[int, int]
Matching = List[Edge]

def u2_edge(u: int, v: int) -> Edge:
    return (u, v) if u < v else (v, u)

def B(G: nx.Graph, v: int) -> nx.Graph:
    """Deterministic labelled vertex-to-triangle expansion B_v.

    The vertices of G are assumed to be 0,...,n-1.  If the neighbours of v are
    a<b<c, delete va and vb, retain vc, add n,n+1, and add
        vn, v(n+1), n(n+1), na, (n+1)b.
    Thus {v,n,n+1} is the new triangle.
    """
    H = G.copy()
    n = len(H)
    assert set(H) == set(range(n))
    a, b, c = sorted(H.neighbors(v))
    H.remove_edge(v, a)
    H.remove_edge(v, b)
    H.add_nodes_from((n, n + 1))
    H.add_edges_from(((v, n), (v, n + 1), (n, n + 1), (n, a), (n + 1, b)))
    assert all((H.degree(x) == 3 for x in H))
    return H

def u2_extended_prism(word: Sequence[int]) -> nx.Graph:
    """Construct the extended prism P(word) with the standard active end."""
    G = nx.Graph()
    u = [0, 1, 2]
    x = [3, 4, 5]
    G.add_edges_from(((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)))
    G.add_edges_from(((u[i], x[i]) for i in range(3)))
    nxt = 6
    for symbol in word:
        s = symbol - 1
        old = list(x)
        root = old[s]
        outside = [z for z in G.neighbors(root) if z not in old]
        assert len(outside) == 1
        y = outside[0]
        new = [nxt, nxt + 1, nxt + 2]
        nxt += 3
        G.remove_node(root)
        G.add_nodes_from(new)
        G.add_edges_from(((new[0], new[1]), (new[1], new[2]), (new[2], new[0])))
        G.add_edge(new[s], y)
        for j in range(3):
            if j != s:
                G.add_edge(new[j], old[j])
        x = new
    return nx.convert_node_labels_to_integers(G, ordering='sorted')

def perfect_matchings(G: nx.Graph) -> List[Tuple[Edge, ...]]:
    """Enumerate all perfect matchings exactly, in lexicographic order."""
    out: List[Tuple[Edge, ...]] = []

    def rec(unmatched: Set[int], chosen: List[Edge]) -> None:
        if not unmatched:
            out.append(tuple(sorted(chosen)))
            return
        v = min(unmatched)
        for u in sorted(G.neighbors(v)):
            if u in unmatched:
                rec(unmatched - {v, u}, chosen + [u2_edge(v, u)])
    rec(set(G), [])
    return sorted(set(out))

def one_perfect_matching(G: nx.Graph) -> Matching | None:
    """Return the lexicographically first perfect matching, or None."""

    def rec(unmatched: Set[int], chosen: List[Edge]) -> Matching | None:
        if not unmatched:
            return sorted(chosen)
        v = min(unmatched)
        for u in sorted(G.neighbors(v)):
            if u in unmatched:
                ans = rec(unmatched - {v, u}, chosen + [u2_edge(v, u)])
                if ans is not None:
                    return ans
        return None
    if len(G) % 2:
        return None
    return rec(set(G), [])

def lonely_edges(G: nx.Graph) -> Set[Edge]:
    counts = {u2_edge(u, v): 0 for u, v in G.edges()}
    for M in perfect_matchings(G):
        for e in M:
            counts[e] += 1
    return {e for e, c in counts.items() if c == 1}

def triangles(G: nx.Graph) -> List[Tuple[int, int, int]]:
    ans = set()
    for u in G:
        for v, w in combinations(sorted(G.neighbors(u)), 2):
            if G.has_edge(v, w):
                ans.add(tuple(sorted((u, v, w))))
    return sorted(ans)

def contract_triangle(G: nx.Graph, T: Sequence[int]) -> nx.Graph:
    Tset = set(T)
    external: List[int] = []
    for x in Tset:
        outside = [y for y in G.neighbors(x) if y not in Tset]
        assert len(outside) == 1
        external.append(outside[0])
    assert len(set(external)) == 3
    H = G.copy()
    H.remove_nodes_from(Tset)
    z = max(G) + 1
    H.add_node(z)
    H.add_edges_from(((z, y) for y in external))
    return nx.convert_node_labels_to_integers(H, ordering='sorted')

def sigma(G: nx.Graph, v: int) -> Set[Edge]:
    """Compute Sigma_G(v) using the deletion-perfect-matching criterion."""
    L = lonely_edges(G)
    closed = {v, *G.neighbors(v)}
    ans: Set[Edge] = set()
    for x, y in L:
        if v in (x, y) or x in closed or y in closed:
            continue
        H = G.copy()
        H.remove_nodes_from(closed | {x, y})
        if one_perfect_matching(H) is not None:
            ans.add((x, y))
    return ans

def positive_certificate(G: nx.Graph, v: int, e: Edge) -> Matching:
    closed = {v, *G.neighbors(v)}
    x, y = e
    H = G.copy()
    H.remove_nodes_from(closed | {x, y})
    M = one_perfect_matching(H)
    assert M is not None
    return M

def tutte_witness(G: nx.Graph) -> Dict[str, object] | None:
    """Find a Tutte obstruction: odd(G-S)>|S|, by exhaustive search."""
    vertices = sorted(G)
    for k in range(len(vertices) + 1):
        for S in combinations(vertices, k):
            H = G.copy()
            H.remove_nodes_from(S)
            odd = [sorted(C) for C in nx.connected_components(H) if len(C) % 2]
            if len(odd) > k:
                return {'S': list(S), 'odd_components': odd}
    return None

def status_certificate(G: nx.Graph, v: int, e: Edge) -> Dict[str, object]:
    closed = {v, *G.neighbors(v)}
    x, y = e
    if v in e:
        return {'status': 'incident_with_root'}
    if x in closed or y in closed:
        return {'status': 'endpoint_in_closed_neighbourhood'}
    H = G.copy()
    H.remove_nodes_from(closed | {x, y})
    M = one_perfect_matching(H)
    if M is not None:
        return {'status': 'in_sigma', 'perfect_matching': M}
    witness = tutte_witness(H)
    assert witness is not None
    return {'status': 'not_in_sigma', 'tutte_witness': witness}

def iso_classes(items: Iterable[Tuple[int, nx.Graph]]) -> List[List[Tuple[int, nx.Graph]]]:
    reps: List[nx.Graph] = []
    classes: List[List[Tuple[int, nx.Graph]]] = []
    for item in items:
        _, G = item
        for i, H in enumerate(reps):
            if nx.is_isomorphic(G, H):
                classes[i].append(item)
                break
        else:
            reps.append(G)
            classes.append([item])
    return classes

def identify(G: nx.Graph, registry: Dict[str, nx.Graph]) -> List[str]:
    return [name for name, H in registry.items() if len(G) == len(H) and nx.is_isomorphic(G, H)]

def adjacency(G: nx.Graph) -> Dict[str, List[int]]:
    return {str(v): sorted(G.neighbors(v)) for v in sorted(G)}

def canonical_word(word: Sequence[int]) -> Tuple[int, ...]:
    candidates = []
    for p in permutations((1, 2, 3)):
        mp = {1: p[0], 2: p[1], 3: p[2]}
        w = tuple((mp[x] for x in word))
        candidates.extend((w, tuple(reversed(w))))
    return min(candidates)

def main_u2_kernels() -> None:
    K4 = nx.complete_graph(4)
    Pr = B(K4, 0)
    bicorn = B(Pr, 0)
    T0 = B(bicorn, 4)
    T1 = B(T0, 0)
    T2 = B(T1, 2)
    T3 = B(T2, 9)
    D0 = B(T0, 1)
    D1 = B(T1, 10)
    D2 = B(T1, 0)
    graphs = {'K4': K4, 'Pr': Pr, 'bicorn': bicorn, 'T0': T0, 'T1': T1, 'T2': T2, 'T3': T3, 'D0': D0, 'D1': D1, 'D2': D2}
    expected_lonely = {'T0': {(1, 3), (4, 8), (6, 7)}, 'T1': {(1, 3), (4, 8), (6, 7)}, 'T2': {(1, 3), (4, 8), (6, 7)}, 'T3': {(1, 3), (4, 8), (6, 7)}, 'D0': {(1, 10), (4, 8)}, 'D1': {(1, 3), (4, 8)}, 'D2': {(1, 3), (6, 7)}}
    for name, L in expected_lonely.items():
        assert lonely_edges(graphs[name]) == L, (name, lonely_edges(graphs[name]))
    upper_children = {}
    for name in ('K4', 'Pr', 'bicorn'):
        G = graphs[name]
        items = [(v, B(G, v)) for v in sorted(G)]
        classes = iso_classes(items)
        upper_children[name] = [{'roots': [v for v, _ in C], 'child_order': len(C[0][1]), 'lonely_edge_count': len(lonely_edges(C[0][1]))} for C in classes]
    assert upper_children['K4'] == [{'roots': [0, 1, 2, 3], 'child_order': 6, 'lonely_edge_count': 6}]
    assert upper_children['Pr'] == [{'roots': [0, 1, 2, 3, 4, 5], 'child_order': 8, 'lonely_edge_count': 5}]
    assert sorted((x['lonely_edge_count'] for x in upper_children['bicorn'])) == [3, 4, 4]
    T = [T0, T1, T2, T3]
    sigma_partitions = {}
    sigma_certificates = {}
    expected_partitions = {'T0': {'0': [0, 2, 9], '1': [1, 3, 4, 6, 7, 8], '3': [5]}, 'T1': {'0': [2, 9], '1': [0, 1, 3, 4, 6, 7, 8, 10, 11], '3': [5]}, 'T2': {'0': [9], '1': [0, 1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 13], '3': [5]}, 'T3': {'0': [], '1': [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], '3': [5]}}
    for i, G in enumerate(T):
        name = f'T{i}'
        part: Dict[str, List[int]] = defaultdict(list)
        certs = {}
        for v in sorted(G):
            S = sigma(G, v)
            part[str(len(S))].append(v)
            certs[str(v)] = {'sigma': [list(e) for e in sorted(S)], 'lonely_edges': {str(e): status_certificate(G, v, e) for e in sorted(lonely_edges(G))}}
        sigma_partitions[name] = {k: list(part.get(k, [])) for k in ('0', '1', '2', '3')}
        sigma_partitions[name] = {k: vals for k, vals in sigma_partitions[name].items() if vals or k in expected_partitions[name]}
        sigma_certificates[name] = certs
        assert sigma_partitions[name] == expected_partitions[name]
    expected_u3_roots = {'T0': [0, 2, 9], 'T1': [2, 9], 'T2': [9], 'T3': []}
    u3_child_classes = {}
    for i, G in enumerate(T):
        name = f'T{i}'
        items = [(v, B(G, v)) for v in sorted(G) if len(lonely_edges(B(G, v))) == 3]
        classes = iso_classes(items)
        u3_child_classes[name] = [[v for v, _ in C] for C in classes]
        roots = sorted((v for C in classes for v, _ in C))
        assert roots == expected_u3_roots[name]
    D0_children = {v: B(D0, v) for v in sorted(D0) if len(sigma(D0, v)) == 0}
    assert sorted(D0_children) == [0, 1, 2, 8, 9, 11]
    order14_registry: Dict[str, nx.Graph] = {'D1': D1, 'D2': D2}
    for pat in ('1121', '1122', '1212', '1213', '1231', '1221', '1223'):
        order14_registry[f'P({pat})'] = u2_extended_prism(tuple(map(int, pat)))
    for v, H in D0_children.items():
        order14_registry[f'D0^{v}'] = H
    assert len(order14_registry) == 15
    for a, b in combinations(order14_registry, 2):
        assert not nx.is_isomorphic(order14_registry[a], order14_registry[b]), (a, b)
    order12_registry: Dict[str, nx.Graph] = {'D0': D0}
    order16_registry: Dict[str, nx.Graph] = {f'T2^{v}': B(T2, v) for v in (0, 1, 2, 3, 4, 11)}
    parent_registries = {12: order12_registry, 14: order14_registry, 16: order16_registry}
    u2_child_classes = {}
    known_D = {'D0': D0, 'D1': D1, 'D2': D2}
    for i, G in enumerate(T):
        name = f'T{i}'
        items = [(v, B(G, v)) for v in sorted(G) if len(lonely_edges(B(G, v))) == 2]
        classes = iso_classes(items)
        rows = []
        for C in classes:
            rep, H = C[0]
            other_parents = []
            new_triangle = tuple(sorted((rep, len(G), len(G) + 1)))
            for tri in triangles(H):
                P = contract_triangle(H, tri)
                if len(lonely_edges(P)) == 2:
                    types = identify(P, parent_registries.get(len(P), {}))
                    other_parents.append({'triangle': list(tri), 'types': types})
            rows.append({'representative_root': rep, 'roots': [v for v, _ in C], 'known_kernel': (identify(H, known_D) or [None])[0], 'new_triangle': list(new_triangle), 'other_U2_parents': other_parents})
        u2_child_classes[name] = rows
    assert [r['roots'] for r in u2_child_classes['T0']] == [[1, 3, 4, 6, 7, 8]]
    assert [r['roots'] for r in u2_child_classes['T1']] == [[0, 11], [1, 8], [3, 4], [6, 7], [10]]
    assert [r['roots'] for r in u2_child_classes['T2']] == [[0, 12], [1, 7], [2, 10], [3, 6], [4, 8], [11, 13]]
    assert [r['roots'] for r in u2_child_classes['T3']] == [[0, 9, 11, 12, 13, 14], [1, 3, 4, 6, 7, 8], [2, 10, 15]]
    assert u2_child_classes['T0'][0]['known_kernel'] == 'D0'
    assert u2_child_classes['T1'][0]['known_kernel'] == 'D2'
    assert u2_child_classes['T1'][-1]['known_kernel'] == 'D1'
    for row in u2_child_classes['T0']:
        if row['known_kernel'] == 'D0':
            assert not row['other_U2_parents']
    for row in u2_child_classes['T1']:
        if row['known_kernel'] in {'D1', 'D2'}:
            assert not row['other_U2_parents']
        else:
            assert row['other_U2_parents']
    for name in ('T2', 'T3'):
        assert all((row['other_U2_parents'] for row in u2_child_classes[name]))
    small_registry = {'T0': T0, 'T1': T1, 'P(11)': u2_extended_prism((1, 1)), 'P(12)': u2_extended_prism((1, 2)), 'P(112)': u2_extended_prism((1, 1, 2)), 'P(121)': u2_extended_prism((1, 2, 1)), 'P(123)': u2_extended_prism((1, 2, 3))}
    D_parents = {}
    for name, G in (('D0', D0), ('D1', D1), ('D2', D2)):
        rows = []
        for tri in triangles(G):
            P = contract_triangle(G, tri)
            rows.append({'triangle': list(tri), 'lonely_edge_count': len(lonely_edges(P)), 'types': identify(P, small_registry)})
        D_parents[name] = rows
    assert [r['types'] for r in D_parents['D0']] == [['P(11)'], ['T0'], ['P(12)']]
    assert [r['types'] for r in D_parents['D1']] == [['P(112)'], ['P(112)'], ['T1']]
    assert [r['types'] for r in D_parents['D2']] == [['T1'], ['P(121)'], ['P(123)']]
    representatives = sorted({canonical_word(w) for w in product((1, 2, 3), repeat=4)})
    length4_table = []
    expected_counts = {'1111': 4, '1112': 3, '1121': 2, '1122': 2, '1123': 3, '1212': 2, '1213': 2, '1221': 2, '1223': 2, '1231': 2}
    for w in representatives:
        G = u2_extended_prism(w)
        key = ''.join(map(str, w))
        row = {'pattern': key, 'perfect_matching_count': len(perfect_matchings(G)), 'lonely_edge_count': len(lonely_edges(G))}
        length4_table.append(row)
        assert row['lonely_edge_count'] == expected_counts[key]
    data = {'software': {'python': '3.x', 'networkx': nx.__version__}, 'graphs': {name: {'order': len(G), 'adjacency': adjacency(G), 'triangles': [list(t) for t in triangles(G)], 'lonely_edges': [list(e) for e in sorted(lonely_edges(G))], 'perfect_matching_count': len(perfect_matchings(G))} for name, G in graphs.items()}, 'upper_children': upper_children, 'sigma_partitions': sigma_partitions, 'sigma_certificates': sigma_certificates, 'u3_child_classes': u3_child_classes, 'u2_child_classes': u2_child_classes, 'D_parents': D_parents, 'length4_table': length4_table}
    out = OUTPUT_DIR / 'u2_finite_certificates.json'
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('All assertions passed.')
    print(f'Wrote {out}')
    print('Sigma partitions:')
    for name, part in sigma_partitions.items():
        print(f'  {name}: {part}')
    print('Length-four table:')
    for row in length4_table:
        print('  {pattern}: pm={perfect_matching_count}, lonely={lonely_edge_count}'.format(**row))
'===== MARKED CONSTRUCTION CHECKS ====='
Edge = frozenset

def E(u, v):
    return frozenset((u, v))

class PMOracle:

    def __init__(self, G: nx.Graph):
        self.G = G
        self.V = tuple(sorted(G.nodes(), key=repr))
        self.idx = {v: i for i, v in enumerate(self.V)}
        self.n = len(self.V)
        self.full = (1 << self.n) - 1
        self.adj = [0] * self.n
        for v in self.V:
            m = 0
            for w in G.neighbors(v):
                m |= 1 << self.idx[w]
            self.adj[self.idx[v]] = m

    @lru_cache(None)
    def count_mask(self, mask: int) -> int:
        if mask == 0:
            return 1
        if mask.bit_count() % 2:
            return 0
        i = (mask & -mask).bit_length() - 1
        nbr = self.adj[i] & mask
        total = 0
        while nbr:
            b = nbr & -nbr
            j = b.bit_length() - 1
            total += self.count_mask(mask & ~(1 << i) & ~(1 << j))
            nbr -= b
        return total

    def count_after_remove(self, removed) -> int:
        m = self.full
        for v in removed:
            if v in self.idx:
                m &= ~(1 << self.idx[v])
        return self.count_mask(m)

    def edge_count(self, u, v) -> int:
        return self.count_after_remove({u, v})

    def lonely(self):
        return {E(u, v) for u, v in self.G.edges() if self.edge_count(u, v) == 1}

    def unique_matching(self, e):
        a, b = tuple(e)
        mask = self.full & ~(1 << self.idx[a]) & ~(1 << self.idx[b])
        out = {e}
        assert self.count_mask(mask) == 1
        while mask:
            i = (mask & -mask).bit_length() - 1
            nbr = self.adj[i] & mask
            chosen = None
            while nbr:
                bit = nbr & -nbr
                j = bit.bit_length() - 1
                if self.count_mask(mask & ~(1 << i) & ~(1 << j)):
                    chosen = j
                    break
                nbr -= bit
            assert chosen is not None
            out.add(E(self.V[i], self.V[chosen]))
            mask &= ~(1 << i) & ~(1 << chosen)
        return frozenset(out)

def info(G):
    O = PMOracle(G)
    L = O.lonely()
    assert len(L) == 2
    Ls = tuple(sorted(L, key=lambda e: repr(sorted(e, key=repr))))
    M = {e: O.unique_matching(e) for e in Ls}
    typ = '=' if M[Ls[0]] == M[Ls[1]] else '!='
    safe = set()
    for v in G:
        C = {v, *G.neighbors(v)}
        if all((set(e) & C or O.count_after_remove(C | set(e)) == 0 for e in L)):
            safe.add(v)
    return (O, Ls, M, typ, safe)

def rjoin_contains(G, O, R, e):
    R = set(R)
    if set(e) & R:
        return True
    for z in set(G) - R:
        if len(set(G.neighbors(z)) & R) >= 2:
            return False
    a, b = tuple(e)
    if set(G.neighbors(a)) & R or set(G.neighbors(b)) & R:
        return False
    rem = {z for z in G if z not in R and (not set(G.neighbors(z)) & R)}
    if a not in rem or b not in rem:
        return False
    return O.count_after_remove(set(G) - rem | {a, b}) > 0

def verify_noninterference(G, A, L, O):
    A = tuple(sorted(A, key=repr))
    for k in range(1, len(A) + 1):
        for R in combinations(A, k):
            for e in L:
                if set(e).isdisjoint(R):
                    assert not rjoin_contains(G, O, R, e), (R, e)

def marked_extended_prism(word):
    G = nx.Graph()
    U = {i: ('u', i) for i in (1, 2, 3)}
    X = {i: ('x', 0, i) for i in (1, 2, 3)}
    G.add_edges_from([(U[1], U[2]), (U[2], U[3]), (U[3], U[1]), (X[1], X[2]), (X[2], X[3]), (X[3], X[1])])
    G.add_edges_from(((U[i], X[i]) for i in (1, 2, 3)))
    for s_idx, s in enumerate(word, 1):
        old = dict(X)
        root = old[s]
        out = [z for z in G.neighbors(root) if z not in old.values()]
        assert len(out) == 1
        y = out[0]
        G.remove_node(root)
        X = {i: ('x', s_idx, i) for i in (1, 2, 3)}
        G.add_edges_from([(X[1], X[2]), (X[2], X[3]), (X[3], X[1]), (X[s], y)])
        G.add_edges_from(((X[j], old[j]) for j in (1, 2, 3) if j != s))
    return (G, X)

def expand(G, v):
    H = G.copy()
    nbr = tuple(G.neighbors(v))
    child = {x: ('new', repr(v), repr(x), len(G)) for x in nbr}
    H.remove_node(v)
    H.add_nodes_from(child.values())
    C = list(child.values())
    H.add_edges_from([(C[0], C[1]), (C[1], C[2]), (C[2], C[0])])
    H.add_edges_from(((child[x], x) for x in nbr))
    return (H, child)

def predicted_child_active(G, v, L, M):
    ans = set()
    for x in G.neighbors(v):
        if all((v in e or E(v, x) not in M[e] for e in L)):
            ans.add(x)
    return ans

def finite_seeds():
    K4 = nx.complete_graph(4)
    Pr = B(K4, 0)
    bic = B(Pr, 0)
    T0 = B(bic, 4)
    T1 = B(T0, 0)
    data = {'D0': (B(T0, 1), {0, 1, 2, 8, 9, 11}), 'D1': (B(T1, 10), {1, 2, 8, 9, 13}), 'D2': (B(T1, 0), {2, 3, 6, 9, 12})}
    expected = {'1121': {('u', 1), ('x', 2, 3), ('x', 3, 3), ('x', 4, 2)}, '1122': {('u', 1), ('u', 2), ('x', 4, 1), ('x', 4, 2)}, '1212': {('u', 1), ('x', 1, 3), ('x', 2, 3), ('x', 4, 2)}, '1213': {('u', 3), ('x', 0, 2), ('x', 1, 3), ('x', 2, 2), ('x', 4, 3)}, '1221': {('u', 1), ('u', 3), ('x', 4, 1), ('x', 4, 3)}, '1223': {('u', 3), ('x', 0, 2), ('x', 1, 3), ('x', 2, 1), ('x', 3, 2), ('x', 4, 1)}, '1231': {('u', 1), ('u', 3), ('x', 4, 1), ('x', 4, 2)}}
    for w, A in expected.items():
        data['P(' + w + ')'] = (marked_extended_prism(tuple(map(int, w)))[0], A)
    return data

def infinite_expected(r, t):
    G, X = marked_extended_prism((1,) + (2,) * r + (t,))
    final = r + 2
    equal = t == 1 and r % 2 == 0 or (t == 3 and r % 2 == 1)
    if equal:
        A = {('u', 1), ('u', 3), ('x', final, 1), ('x', final, 3)}
    else:
        A = {('x', 0, 2), ('x', r + 1, 2), ('u', 3), ('x', final, 4 - t)}
        A.update((('x', k, 3 if k % 2 else 1) for k in range(1, r + 1)))
    return (G, A, equal)

def check_seed(name, G, A, records):
    O, L, M, t, S = info(G)
    assert S == set(A), (name, S, A)
    verify_noninterference(G, A, L, O)
    records[name] = {'order': len(G), 'type': t, 'lonely_edges': [sorted(map(str, e)) for e in L], 'active_count': len(A)}
    for v in A:
        H, ch = expand(G, v)
        OH, LH, MH, tH, SH = info(H)
        mate = {u for u in A - {v} if G.has_edge(u, v) and E(u, v) in L}
        new_by_nbr = predicted_child_active(G, v, L, M)
        expected = set(A) - {v} - mate | {ch[x] for x in new_by_nbr}
        assert SH == expected, (name, v, SH, expected)
        assert tH == t

def main_marked_construction():
    records = {}
    for name, (G, A) in finite_seeds().items():
        check_seed(name, G, A, records)
    inf = []
    for r in range(2, 11):
        for t in (1, 3):
            G, A, eq = infinite_expected(r, t)
            O, L, M, typ, S = info(G)
            assert S == A, (r, t, S, A)
            assert (typ == '=') == eq
            verify_noninterference(G, A, L, O)
            inf.append({'r': r, 't': t, 'type': typ, 'order': len(G), 'active_count': len(A)})
    out = {'finite_seeds': records, 'infinite_samples': inf}
    (OUTPUT_DIR / 'marked_construction_certificates.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('All marked constructive assertions passed.')
'===== STANDARD MARKING CHECKS ====='

def incident_choice(M, G, v):
    """Return the unique matching edge incident with v."""
    choices = [E(v, u) for u in G.neighbors(v) if E(v, u) in M]
    assert len(choices) == 1
    return choices[0]

def edge_set(path):
    return {E(path[i], path[i + 1]) for i in range(len(path) - 1)}

def verify_common_mark(G, lonely_edges, triangles, active):
    O, Ls, M, typ, safe = info(G)
    L = set(Ls)
    assert typ == '='
    assert L == set(lonely_edges)
    assert safe == set(active)
    for e, tri in zip(lonely_edges, triangles):
        tri = tuple(tri)
        assert set(e).issubset(tri)
        assert all((G.has_edge(tri[i], tri[(i + 1) % 3]) for i in range(3)))
    verify_noninterference(G, active, L, O)
    return (O, Ls, M)

def verify_unequal_mark(G, path, tips):
    """tips is a dict root -> direction."""
    O, Ls, M, typ, safe = info(G)
    assert typ == '!='
    x, v, w, y = path
    assert all((G.has_edge(path[i], path[i + 1]) for i in range(3)))
    alpha, beta = (E(x, v), E(w, y))
    assert set(Ls) == {alpha, beta}
    assert safe == {v, w, *tips.keys()}
    assert incident_choice(M[alpha], G, v) == alpha
    t = next((z for z in G.neighbors(v) if z not in {x, w}))
    assert incident_choice(M[beta], G, v) == E(v, t)
    assert incident_choice(M[beta], G, w) == beta
    s = next((z for z in G.neighbors(w) if z not in {v, y}))
    assert incident_choice(M[alpha], G, w) == E(w, s)
    assert E(v, w) not in M[alpha] and E(v, w) not in M[beta]
    for u, p in tips.items():
        assert p in G.neighbors(u)
        assert p not in safe
        others = [z for z in G.neighbors(u) if z != p]
        assert len(others) == 2
        assert E(u, p) not in M[alpha] and E(u, p) not in M[beta]
        choices = {incident_choice(M[alpha], G, u), incident_choice(M[beta], G, u)}
        assert choices == {E(u, others[0]), E(u, others[1])}
    verify_noninterference(G, safe, set(Ls), O)
    return (O, Ls, M)

def common_child_mark(G, lonely_edges, triangles, root):
    H, ch = expand(G, root)
    idx = next((i for i, e in enumerate(lonely_edges) if root in e))
    e = lonely_edges[idx]
    other_endpoint = next((z for z in e if z != root))
    tri = triangles[idx]
    third = next((z for z in tri if z not in e))
    outside = next((z for z in G.neighbors(root) if z not in {other_endpoint, third}))
    new_e = E(ch[third], ch[outside])
    new_tri = (ch[other_endpoint], ch[third], ch[outside])
    new_edges = list(lonely_edges)
    new_tris = list(triangles)
    new_edges[idx] = new_e
    new_tris[idx] = new_tri
    active = set().union(*[set(z) for z in new_edges])
    verify_common_mark(H, new_edges, new_tris, active)

def center_child_mark(G, path, tips, left=True):
    x, v, w, y = path
    if not left:
        rpath = (y, w, v, x)
        H, rnew_path, rnew_tips = center_child_mark_data(G, rpath, tips)
        return (H, tuple(reversed(rnew_path)), rnew_tips)
    return center_child_mark_data(G, path, tips)

def center_child_mark_data(G, path, tips):
    x, v, w, y = path
    t = next((z for z in G.neighbors(v) if z not in {x, w}))
    H, ch = expand(G, v)
    new_path = (ch[t], ch[w], w, y)
    new_tips = dict(tips)
    new_tips[ch[x]] = ch[t]
    verify_unequal_mark(H, new_path, new_tips)
    return (H, new_path, new_tips)

def tip_child_mark(G, path, tips, root):
    p = tips[root]
    H, ch = expand(G, root)
    new_tips = dict(tips)
    del new_tips[root]
    new_tips[ch[p]] = p
    verify_unequal_mark(H, path, new_tips)
    return (H, path, new_tips)

def finite_mark_data():
    K4 = nx.complete_graph(4)
    Pr = B(K4, 0)
    bic = B(Pr, 0)
    T0 = B(bic, 4)
    T1 = B(T0, 0)
    data = {}
    data['D0'] = ('!=', B(T0, 1), (10, 1, 8, 4), {0: 5, 2: 3, 9: 4, 11: 10})
    data['D1'] = ('!=', B(T1, 10), (3, 1, 8, 4), {2: 3, 9: 4, 13: 5})
    data['D2'] = ('!=', B(T1, 0), (1, 3, 6, 7), {2: 1, 9: 5, 12: 7})
    common = {'P(1122)': ((E(('u', 1), ('u', 2)), E(('x', 4, 1), ('x', 4, 2))), ((('u', 1), ('u', 2), ('u', 3)), (('x', 4, 1), ('x', 4, 2), ('x', 4, 3)))), 'P(1221)': ((E(('u', 1), ('u', 3)), E(('x', 4, 1), ('x', 4, 3))), ((('u', 1), ('u', 2), ('u', 3)), (('x', 4, 1), ('x', 4, 2), ('x', 4, 3)))), 'P(1231)': ((E(('u', 1), ('u', 3)), E(('x', 4, 1), ('x', 4, 2))), ((('u', 1), ('u', 2), ('u', 3)), (('x', 4, 1), ('x', 4, 2), ('x', 4, 3))))}
    for name, (edges, tris) in common.items():
        word = tuple(map(int, name[2:-1]))
        G, _ = marked_extended_prism(word)
        data[name] = ('=', G, edges, tris)
    unequal = {'P(1121)': ((('x', 2, 1), ('x', 2, 3), ('x', 3, 3), ('x', 3, 2)), {('u', 1): ('x', 2, 1), ('x', 4, 2): ('x', 3, 2)}), 'P(1212)': ((('x', 1, 1), ('x', 1, 3), ('x', 2, 3), ('x', 2, 2)), {('u', 1): ('x', 1, 1), ('x', 4, 2): ('x', 2, 2)}), 'P(1213)': ((('x', 0, 3), ('x', 0, 2), ('x', 2, 2), ('x', 2, 3)), {('u', 3): ('x', 0, 3), ('x', 1, 3): ('x', 1, 1), ('x', 4, 3): ('x', 2, 3)}), 'P(1223)': ((('x', 0, 3), ('x', 0, 2), ('x', 3, 2), ('x', 3, 1)), {('u', 3): ('x', 0, 3), ('x', 1, 3): ('x', 1, 1), ('x', 2, 1): ('x', 2, 3), ('x', 4, 1): ('x', 3, 1)})}
    for name, (path, tips) in unequal.items():
        word = tuple(map(int, name[2:-1]))
        G, _ = marked_extended_prism(word)
        data[name] = ('!=', G, path, tips)
    return data

def infinite_mark(r, t):
    G, _ = marked_extended_prism((1,) + (2,) * r + (t,))
    final = r + 2
    equal = t == 1 and r % 2 == 0 or (t == 3 and r % 2 == 1)
    if equal:
        edges = (E(('u', 1), ('u', 3)), E(('x', final, 1), ('x', final, 3)))
        tris = ((('u', 1), ('u', 2), ('u', 3)), (('x', final, 1), ('x', final, 2), ('x', final, 3)))
        return ('=', G, edges, tris)
    path = (('x', 0, 3), ('x', 0, 2), ('x', r + 1, 2), ('x', r + 1, 4 - t))
    tips = {('u', 3): ('x', 0, 3), ('x', final, 4 - t): ('x', r + 1, 4 - t)}
    for k in range(1, r + 1):
        eta = 3 if k % 2 else 1
        tips['x', k, eta] = ('x', k, 4 - eta)
    return ('!=', G, path, tips)

def main_revised_sections():
    report = {'finite': {}, 'infinite': []}
    for name, item in finite_mark_data().items():
        typ, G, a, b = item
        if typ == '=':
            edges, tris = (a, b)
            active = set().union(*[set(e) for e in edges])
            verify_common_mark(G, edges, tris, active)
            for root in active:
                common_child_mark(G, edges, tris, root)
            report['finite'][name] = {'type': '=', 'order': len(G), 'active_count': len(active), 'checked_E_roots': len(active)}
        else:
            path, tips = (a, b)
            verify_unequal_mark(G, path, tips)
            center_child_mark(G, path, tips, True)
            center_child_mark(G, path, tips, False)
            for root in tips:
                tip_child_mark(G, path, tips, root)
            report['finite'][name] = {'type': '!=', 'order': len(G), 'active_count': len(tips) + 2, 'checked_C_roots': 2, 'checked_T_roots': len(tips)}
    for r in range(2, 13):
        for t in (1, 3):
            typ, G, a, b = infinite_mark(r, t)
            if typ == '=':
                edges, tris = (a, b)
                active = set().union(*[set(e) for e in edges])
                verify_common_mark(G, edges, tris, active)
            else:
                path, tips = (a, b)
                verify_unequal_mark(G, path, tips)
                active = {path[1], path[2], *tips.keys()}
            report['infinite'].append({'r': r, 't': t, 'type': typ, 'order': len(G), 'active_count': len(active)})
    out = OUTPUT_DIR / 'revised_sections_7_9_certificates.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('All revised Sections 7--9 assertions passed.')
'===== INFINITE TRANSFER CHECKS ====='
State = tuple[int, int]
ZERO = (0, 0)
TOP = (1, 0)
BOT = (0, 1)
BOTH = (1, 1)

def theta(j: int) -> State:
    return BOT if j % 2 else TOP

def bartheta(j: int) -> State:
    a, b = theta(j)
    return (1 - a, 1 - b)

def local_solutions(roots: set[str], inp: State, out: State):
    sols = []
    for h in (0, 1):
        da = inp[0] + out[0] + h
        db = inp[1] + out[1] + h
        if da == (3 if 'a' in roots else 1) and db == (3 if 'b' in roots else 1):
            sols.append(h)
    return sols

def check_local_tables():
    states = [ZERO, BOT, TOP, BOTH]
    got = []
    for roots in [set(), {'a'}, {'b'}, {'a', 'b'}]:
        for i in states:
            for o in states:
                for h in local_solutions(roots, i, o):
                    got.append((tuple(sorted(roots)), i, o, h))
    exp = [((), ZERO, ZERO, 1), ((), ZERO, BOTH, 0), ((), BOT, TOP, 0), ((), TOP, BOT, 0), ((), BOTH, ZERO, 0), (('a',), TOP, TOP, 1), (('b',), BOT, BOT, 1), (('a', 'b'), BOTH, BOTH, 1)]
    assert sorted(got) == sorted(exp), (got, exp)
    for first_active in ('a', 'b'):
        second_active = 'b' if first_active == 'a' else 'a'
        e1 = TOP if first_active == 'a' else BOT
        e2 = TOP if second_active == 'a' else BOT
        relations = {}
        for bits in product((0, 1), repeat=2):
            pairs = set()
            for i in states:
                for mid in states:
                    for o in states:
                        r1 = {first_active} if bits[0] else set()
                        r2 = {second_active} if bits[1] else set()
                        if local_solutions(r1, i, mid) and local_solutions(r2, mid, o):
                            pairs.add((i, o))
            relations[bits] = pairs
        exp00 = {(ZERO, ZERO), (ZERO, BOTH), (BOT, BOT), (TOP, TOP), (BOTH, ZERO), (BOTH, BOTH)}
        assert relations[0, 0] == exp00
        assert relations[1, 0] == {(e1, e2)}
        assert relations[0, 1] == {(e1, e2)}
        assert relations[1, 1] == set()

def infinite_edge(G, u, v):
    assert G.has_edge(u, v), (u, v)
    return E(u, v)

def labels(r, t):
    q = 4 - t
    u1 = ('u', 1)
    u2 = ('u', 2)
    u3 = ('u', 3)
    cL = ('x', 0, 2)
    b0 = ('x', 0, 3)
    cR = ('x', r + 1, 2)
    o = ('x', r + 1, q)
    f = ('x', r + 2, q)
    h = ('x', r + 2, 2)
    g = ('x', r + 2, t)
    a = lambda k: ('x', k, 1)
    b = lambda k: ('x', k, 3)
    y = {t: g, q: o}
    return locals()

def cap_config(G, r, t, name):
    z = labels(r, t)
    u1 = z['u1']
    u2 = z['u2']
    u3 = z['u3']
    cL = z['cL']
    b0 = z['b0']
    cR = z['cR']
    o = z['o']
    f = z['f']
    h = z['h']
    g = z['g']
    a = z['a']
    b = z['b']
    q = z['q']
    p1 = infinite_edge(G, u1, a(1))
    p3 = infinite_edge(G, b0, b(1))
    mu = infinite_edge(G, cL, cR)
    gamma = infinite_edge(G, cL, b0)
    alpha = infinite_edge(G, u1, u3)
    delta = infinite_edge(G, cR, o)
    beta = infinite_edge(G, f, g)
    pq = infinite_edge(G, ('x', r, q), o)
    pt = infinite_edge(G, ('x', r, t), g)
    D = {'L_gamma': {infinite_edge(G, u2, u3), p1, gamma}, 'L_delta': {alpha, infinite_edge(G, u2, cL), p3}, 'L_u1': {infinite_edge(G, u1, u2), alpha, p1, gamma}, 'L_u2': {infinite_edge(G, u1, u2), infinite_edge(G, u2, u3), infinite_edge(G, u2, cL), p3}, 'L_b0': {infinite_edge(G, u1, u2), infinite_edge(G, u3, b0), gamma, p3}, 'L_alpha': {alpha, infinite_edge(G, u2, cL), p3}, 'L_beta': {p1, infinite_edge(G, u2, cL), infinite_edge(G, u3, b0)}, 'L_cL': {alpha, infinite_edge(G, u2, cL), gamma, mu}, 'L_mu': {infinite_edge(G, u1, u2), infinite_edge(G, u3, b0), mu}, 'R_delta': {delta, infinite_edge(G, f, h), pt}, 'R_gamma_t': {infinite_edge(G, o, f), infinite_edge(G, cR, h), pt}, 'R_gamma_q': {infinite_edge(G, cR, h), infinite_edge(G, f, g), pq}, 'R_o': {delta, infinite_edge(G, o, f), infinite_edge(G, h, g), pq}, 'R_h': {infinite_edge(G, cR, h), infinite_edge(G, f, h), infinite_edge(G, h, g), pq}, 'R_g': {delta, infinite_edge(G, h, g), infinite_edge(G, g, f), pt}, 'R_f': {infinite_edge(G, o, f), infinite_edge(G, f, h), infinite_edge(G, f, g), mu}, 'R_cR': {delta, infinite_edge(G, cR, h), infinite_edge(G, f, g), mu}, 'R_beta': {infinite_edge(G, cR, h), beta, pq}, 'R_alpha_t': {infinite_edge(G, o, f), infinite_edge(G, cR, h), pt}, 'R_mu': {infinite_edge(G, o, f), infinite_edge(G, h, g), mu}}
    return D[name]

def states_word(r, kind, k=None):
    if kind == 'theta':
        return [theta(j) for j in range(r + 1)]
    if kind == 'bar':
        return [bartheta(j) for j in range(r + 1)]
    if kind == 'zero':
        return [ZERO] * (r + 1)
    if kind == 'bar_to_theta':
        assert k is not None
        return [bartheta(j) if j < k else theta(j) for j in range(r + 1)]
    if kind == 'theta_to_bar':
        assert k is not None
        return [theta(j) if j < k else bartheta(j) for j in range(r + 1)]
    raise ValueError(kind)

def ladder_edges(G, r, states, root=None):
    J = set()
    a = lambda k: ('x', k, 1)
    b = lambda k: ('x', k, 3)
    z = None
    if root:
        typ, k = root
        eta = 3 if k % 2 else 1
        track = eta if typ == 's' else 4 - eta
        z = ('x', k, track)
    for k in range(1, r + 1):
        inp, out = (states[k - 1], states[k])
        roots = set()
        if z == a(k):
            roots = {'a'}
        elif z == b(k):
            roots = {'b'}
        hs = local_solutions(roots, inp, out)
        assert hs, (k, root, inp, out)
        h = hs[0]
        if h:
            J.add(infinite_edge(G, a(k), b(k)))
    if states[0][0]:
        J.add(infinite_edge(G, ('u', 1), a(1)))
    if states[0][1]:
        J.add(infinite_edge(G, ('x', 0, 3), b(1)))
    for k in range(1, r):
        if states[k][0]:
            J.add(infinite_edge(G, a(k), a(k + 1)))
        if states[k][1]:
            J.add(infinite_edge(G, b(k), b(k + 1)))
    return J

def add_right_boundary(G, J, r, t, state):
    q = 4 - t
    y = {t: ('x', r + 2, t), q: ('x', r + 1, q)}
    if state[0]:
        J.add(infinite_edge(G, ('x', r, 1), y[1]))
    if state[1]:
        J.add(infinite_edge(G, ('x', r, 3), y[3]))

def verify_join(G, J, R):
    for v in G:
        d = sum((1 for e in J if v in e))
        assert d == (3 if v in R else 1), (v, d, R)

def explicit_witnesses(r, t):
    typ, G, a, b = infinite_mark(r, t)
    z = labels(r, t)
    u1 = z['u1']
    u2 = z['u2']
    u3 = z['u3']
    cL = z['cL']
    b0 = z['b0']
    cR = z['cR']
    o = z['o']
    f = z['f']
    h = z['h']
    g = z['g']
    gamma = E(cL, b0)
    delta = E(cR, o)
    alpha = E(u1, u3)
    beta = E(f, g)
    rows = []
    if typ == '=':
        for root, lon, kind, k, L, Rcap, rroot in [(u2, beta, 'bar', None, 'L_u2', 'R_beta', None), (b0, beta, 'bar', None, 'L_b0', 'R_beta', None), (cL, alpha, 'zero', None, 'L_cL', 'R_mu', None), (cR, beta, 'zero', None, 'L_mu', 'R_cR', None), (o, alpha, 'bar', None, 'L_alpha', 'R_o', None), (h, alpha, 'bar', None, 'L_alpha', 'R_h', None)]:
            rows.append((root, lon, kind, k, L, Rcap, rroot))
        for k0 in range(1, r + 1):
            eta = 3 if k0 % 2 else 1
            s = ('x', k0, eta)
            d = ('x', k0, 4 - eta)
            rows.append((s, alpha, 'bar_to_theta', k0, 'L_alpha', 'R_alpha_t', ('s', k0)))
            rows.append((d, beta, 'theta_to_bar', k0, 'L_beta', 'R_beta', ('d', k0)))
    else:
        rows.extend([(u1, gamma, 'theta', None, 'L_u1', 'R_gamma_q', None), (u2, delta, 'bar', None, 'L_u2', 'R_delta', None), (b0, delta, 'bar', None, 'L_b0', 'R_delta', None), (o, gamma, 'theta', None, 'L_gamma', 'R_o', None), (h, gamma, 'theta', None, 'L_gamma', 'R_h', None), (g, delta, 'bar', None, 'L_delta', 'R_g', None)])
        for k0 in range(1, r + 1):
            eta = 3 if k0 % 2 else 1
            d = ('x', k0, 4 - eta)
            rows.append((d, gamma, 'theta_to_bar', k0, 'L_gamma', 'R_gamma_t', ('d', k0)))
    for root, lon, kind, k, L, Rcap, rroot in rows:
        states = states_word(r, kind, k)
        J = set(cap_config(G, r, t, L)) | set(cap_config(G, r, t, Rcap))
        J |= ladder_edges(G, r, states, rroot)
        add_right_boundary(G, J, r, t, states[-1])
        verify_join(G, J, {root})
        assert lon in J and root not in lon, (root, lon)
    return len(rows)

def main_infinite_transfer():
    check_local_tables()
    rec = []
    for r in range(2, 31):
        for t in (1, 3):
            typ, G, a, b = infinite_mark(r, t)
            if typ == '=':
                edges, tris = (a, b)
                active = set().union(*map(set, edges))
                verify_common_mark(G, edges, tris, active)
            else:
                path, tips = (a, b)
                active = {path[1], path[2], *tips.keys()}
                if r <= 12:
                    verify_unequal_mark(G, path, tips)
                else:
                    O, Ls, M, typ0, safe = info(G)
                    assert typ0 == '!=' and safe == active
            nw = explicit_witnesses(r, t)
            assert nw == len(G) - len(active)
            rec.append({'r': r, 't': t, 'type': typ, 'order': len(G), 'active_count': len(active), 'explicit_inactive_witnesses': nw, 'full_subset_check': typ == '=' or r <= 12})
    out = {'local_table': 'passed', 'double_rung_table': 'passed', 'samples': rec}
    (OUTPUT_DIR / 'infinite_transfer_certificates.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('All infinite ladder-transfer assertions passed.')

def choose_output_dir() -> Path:
    parser = argparse.ArgumentParser(description='Run all four U2 verification suites and choose the certificate output directory.')
    parser.add_argument('--output-dir', help='Directory for the four JSON certificates. Relative paths use the current terminal directory.')
    args = parser.parse_args()
    if args.output_dir:
        selected = Path(args.output_dir).expanduser()
    elif sys.stdin.isatty():
        print(f'Certificate output directory [default: {HERE}]')
        typed = input('Enter a path, or press Enter for the default: ').strip()
        selected = Path(typed).expanduser() if typed else HERE
    else:
        selected = HERE
        print(f'Non-interactive input detected; using output directory: {selected}')
    selected = selected.resolve()
    selected.mkdir(parents=True, exist_ok=True)
    return selected

def main():
    global OUTPUT_DIR
    OUTPUT_DIR = choose_output_dir()
    print(f'Certificates will be written to: {OUTPUT_DIR}')
    print('[1/4] finite kernel checks')
    main_u2_kernels()
    print('[2/4] marked construction checks')
    main_marked_construction()
    print('[3/4] standard marking checks')
    main_revised_sections()
    print('[4/4] infinite ladder-transfer checks')
    main_infinite_transfer()
    print('All four verification suites passed.')
if __name__ == '__main__':
    main()
