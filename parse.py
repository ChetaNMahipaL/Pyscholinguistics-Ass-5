#!/usr/bin/env python3
import sys
import math
from collections import defaultdict

class Rule:
    def __init__(self, prob, lhs, rhs):
        self.prob = prob
        self.weight = -math.log2(prob)
        self.lhs = lhs
        self.rhs = rhs
    
    def __repr__(self):
        return f"{self.lhs} -> {' '.join(self.rhs)}"

class State:
    def __init__(self, rule, dot, start_col, end_col, weight, backpointers):
        self.rule = rule
        self.dot = dot
        self.start_col = start_col
        self.end_col = end_col
        self.weight = weight
        self.backpointers = backpointers

    @property
    def is_complete(self):
        return self.dot == len(self.rule.rhs)

    @property
    def next_symbol(self):
        if not self.is_complete:
            return self.rule.rhs[self.dot]
        return None

    @property
    def state_id(self):
        return (self.rule, self.dot, self.start_col)


def get_tree_structure(state):
    """Recursively builds a nested tuple structure: (LHS, [children])"""
    if state.dot == 0:
        return []
    
    if len(state.backpointers) == 2 and isinstance(state.backpointers[1], str):
        prev_state, word = state.backpointers
        return get_tree_structure(prev_state) + [word]
    
    if len(state.backpointers) == 2 and isinstance(state.backpointers[1], State):
        prev_state, completed_state = state.backpointers
        return get_tree_structure(prev_state) + [(completed_state.rule.lhs, get_tree_structure(completed_state))]
    
    return []

def get_all_spans(state):

    spans = []
    spans.append((state.rule.lhs, state.start_col, state.end_col))
    
    curr = state
    while curr and len(curr.backpointers) == 2:
        prev_state, child = curr.backpointers

        if isinstance(child, State):
            spans.extend(get_all_spans(child))
        curr = prev_state
        
    return spans

def format_tree(node, current_indent=0):
    if isinstance(node, str):
        return node
    
    lhs, children = node
    
    if len(children) == 1:
        lhs_str = f"({lhs} "
        child_indent = current_indent + len(lhs_str)
        child_str = format_tree(children[0], child_indent)
        return f"{lhs_str}{child_str})"
    else:
        lhs_str = f"({lhs} "
        child_indent = current_indent + len(lhs_str)
        
        formatted_children = []
        formatted_children.append(format_tree(children[0], child_indent))
        
        for child in children[1:]:
            formatted_children.append("\n" + " " * child_indent + format_tree(child, child_indent))
            
        return lhs_str + "".join(formatted_children) + ")"



def load_grammar(filepath):
    grammar = defaultdict(list)
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split()
            prob = float(parts[0])
            lhs = parts[1]
            rhs = tuple(parts[2:])
            grammar[lhs].append(Rule(prob, lhs, rhs))
    return grammar

def parse_sentence(words, grammar):
    n = len(words)
    chart = [{} for _ in range(n + 1)] 
    
    def add_to_chart(state, col, agenda):
        sid = state.state_id
        if sid not in chart[col] or state.weight < chart[col][sid].weight:
            chart[col][sid] = state
            agenda.append(state)

    agenda = []
    for rule in grammar.get("ROOT", []):
        add_to_chart(State(rule, 0, 0, 0, rule.weight, ()), 0, agenda)

    for i in range(n + 1):
        if i > 0:
            agenda = list(chart[i].values())
        
        while agenda:
            state = agenda.pop(0)
            
            if state.is_complete:
                for customer in list(chart[state.start_col].values()):
                    if not customer.is_complete and customer.next_symbol == state.rule.lhs:
                        new_weight = customer.weight + state.weight
                        new_bp = (customer, state)
                        new_state = State(customer.rule, customer.dot + 1, customer.start_col, i, new_weight, new_bp)
                        add_to_chart(new_state, i, agenda)
            else:
                next_sym = state.next_symbol
                if next_sym in grammar:
                    for rule in grammar[next_sym]:
                        new_state = State(rule, 0, i, i, rule.weight, ())
                        add_to_chart(new_state, i, agenda)
                else:
                    if i < n and words[i] == next_sym:
                        new_state = State(state.rule, state.dot + 1, state.start_col, i + 1, state.weight, (state, words[i]))
                        add_to_chart(new_state, i + 1, [])
                        
    return chart

def main():
    if len(sys.argv) < 3:
        print("Usage: ./parse.py <grammar.gr> <sentences.sen>")
        sys.exit(1)

    grammar_file = sys.argv[1]
    sentences_file = sys.argv[2]
    grammar = load_grammar(grammar_file)

    with open(sentences_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            words = line.split()
            chart = parse_sentence(words, grammar)
            
            best_parse = None
            for state in chart[len(words)].values():
                if state.rule.lhs == "ROOT" and state.is_complete and state.start_col == 0:
                    if best_parse is None or state.weight < best_parse.weight:
                        best_parse = state
            
            if best_parse:

                tree_struct = (best_parse.rule.lhs, get_tree_structure(best_parse))
                print(format_tree(tree_struct))
                
                print(best_parse.weight)
                
                print("Spans:")
                spans = get_all_spans(best_parse)
                spans = sorted(spans, key=lambda x: (x[1], -x[2]))
                for lhs, start, end in spans:
                    print(f"{lhs} [{start}, {end}]")
                print("-" * 20)
            else:
                print("NONE")

if __name__ == "__main__":
    main()