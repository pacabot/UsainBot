"""Minimal S-expression reader/writer for KiCad files."""
import re

def parse(text):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack, cur = [], []
    for t in toks:
        if t == '(':
            new = []; cur.append(new); stack.append(cur); cur = new
        elif t == ')':
            cur = stack.pop()
        else:
            cur.append(t)
    return cur

def name(node):
    return node[0] if node and isinstance(node[0], str) else None

def find_all(node, tag):
    return [c for c in node if isinstance(c, list) and name(c) == tag]

def find(node, tag):
    r = find_all(node, tag)
    return r[0] if r else None

def unq(s):
    if isinstance(s, str) and s.startswith('"'):
        return s[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return s

def dump(node, indent=0):
    pad = '\t' * indent
    if not isinstance(node, list):
        return str(node)
    # leaf-ish node: no sublists -> one line
    if not any(isinstance(c, list) for c in node):
        return pad + '(' + ' '.join(str(c) for c in node) + ')'
    out = [pad + '(' + str(node[0])]
    rest = node[1:]
    scal = []
    i = 0
    while i < len(rest) and not isinstance(rest[i], list):
        scal.append(str(rest[i])); i += 1
    if scal:
        out[0] += ' ' + ' '.join(scal)
    for c in rest[i:]:
        if isinstance(c, list):
            out.append(dump(c, indent + 1))
        else:
            out.append('\t' * (indent + 1) + str(c))
    out.append(pad + ')')
    return '\n'.join(out)
