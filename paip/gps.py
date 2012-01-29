#!/usr/bin/env python

"""
The **General Problem Solver** is a framework for applying *means-ends analysis*
to solve problems that can be specified by a list of initial states, a list of
goal states, and a list of operators that induce state transitions.

Each operator is specified by an action name, a list of precondition states that
must hold before the operator is applied, a list of states that will hold after
the operator is applied (the *add-list*), and a list of states that will no
longer hold after the operator is applied (the *delete-list*).  To achieve a
goal state, GPS uses means-ends analysis: each operator is examined to find one
that contains the goal state in its add-list (it looks for an *appropriate*
operator).  It then tries to achieve all of that operator's precondition states.
If not all of the preconditions can be achieved (the operator is not
*applicable*), then GPS looks for another appropriate operator.  If none exists,
then the goal can't be achieved.  When all of the goal states have been
achieved, the problem is solved.

Problems can be defined in the JSON format by listing the starting states, goal
states, and state transition operators.  An example follows below.

To run GPS on a problem definition, simply

python gps.py problem.json

The sequence of actions that will achieve the goal states will be written to
standard output.

This implementation is inspired by chapter 4 of "Paradigms of Artificial
Intelligence Programming" by Peter Norvig.
"""


__author__ = 'Daniel Connelly'
__email__ = 'dconnelly@gatech.edu'


SIMPLE_PROBLEM = {
    "start": ["son at home", "car needs battery"],
    "finish": ["son at school"],
    "ops": [
        {
            "action": "drive son to school",
            "preconds": ["son at home", "car works"],
            "add": ["son at school"],
            "delete": ["son at home"]
        },
        {
            "action": "shop installs battery",
            "preconds": ["car needs battery"],
            "add": ["car works"],
            "delete": ["car needs battery"]
        }
    ]
}


# === Utility functions ===


def debug(level, msg):
    logging.debug(' %s %s' % (level * '  ', msg))
    

# === Problem solving functions ===


def gps(initial_states, goal_states, operators):
    """
    Find a sequence of operators that will achieve all of the goal states.

    Returns a list of actions that will achieve all of the goal states, or
    None if no such sequence exists.  Each operator is specified by an
    action name, a list of preconditions, an add-list, and a delete-list.
    """

    # To keep track of which operators have been applied, we add additional
    # 'executing ...' states to each operator's add-list.  These will never be
    # deleted by another operator, so when the problem is solved we can find
    # them in the list of current states.
    prefix = 'Executing '
    for operator in operators:
        operator['add'].append(prefix + operator['action'])

    final_states = achieve_all(initial_states, operators, goal_states, [])
    return [state for state in final_states if state.startswith(prefix)]


def achieve_all(states, ops, goals, goal_stack):
    """
    Achieve each state in goals and make sure they still hold at the end.

    The goal stack keeps track of our recursion: which preconditions are we
    trying to satisfy by achieving the specified goals?
    """
    
    # We try to achieve each goal in the order they are given.  If any one
    # goal state cannot be achieved, then the problem cannot be solved.
    for goal in goals:
        states = achieve(states, ops, goal, goal_stack)
        if not states:
            return None

    # We must ensure that we haven't removed a goal state in the process of
    # solving other states--having done so is called the "prerequisite clobbers
    # sibling goal problem".
    for goal in goals:
        if goal not in states:
            return None

    return states
    

def achieve(states, operators, goal, goal_stack):
    """
    Achieve the goal state using means-ends analysis.

    Identifies an appropriate and applicable operator--one that contains the
    goal state in its add-list and has all its preconditions satisified.
    Applies the operator and returns the result.  Returns None if no such
    operator is found or infinite recursion is detected in the goal stack.
    """
    
    debug(len(goal_stack), 'Achieving: %s' % goal)
    
    # Let's check to see if the state already holds before we do anything.
    if goal in states:
        return states

    # Prevent going in circles: look through the goal stack to see if the
    # specified goal appears there.  If so, then we are indirectly trying to
    # achieve goal while already in the process of achieving it.  For example,
    # while trying to achieve state A, we try to achieve state B--a precondition
    # for applying an appropriate operator.  However, to achieve B, we try to
    # satisfy the preconditions for another operator that contains A in its
    # preconditions.
    if goal in goal_stack:
        return None

    for op in operators:
        # Is op appropriate?  Look through its add-list to see if goal is there.
        if goal not in op['add']:
            continue
        # Is op applicable?  Try to apply it--if one of its preconditions cannot
        # be satisifed, then it will return None.
        result = apply_operator(op, states, operators, goal, goal_stack)
        if result:
            return result

    
def apply_operator(operator, states, ops, goal, goal_stack):
    """
    Applies operator and returns the resulting states.

    Achieves all of operator's preconditions and returns the states that hold
    after processing its add-list and delete-list.  If any of its preconditions
    cannot be satisfied, returns None.
    """

    debug(len(goal_stack), 'Consider: %s' % operator['action'])

    # Satisfy all of operator's preconditions.
    result = achieve_all(states, ops, operator['preconds'], [goal] + goal_stack)
    if not result:
        return None

    debug(len(goal_stack), 'Action: %s' % operator['action'])

    # Merge the old states with operator's add-list, filtering out delete-list.
    add_list, delete_list = operator['add'], operator['delete']
    return [state for state in result if state not in delete_list] + add_list


# === Helper functions and setup ===


import sys
import json
import logging


USAGE = 'gps.py [--log=level] problem.json'


def check_usage(args):
    """Check the command line arguments."""

    if len(args) < 1:
        print USAGE
        sys.exit(1)
    

def main(args):
    """Run GPS on the indicated problem file."""

    # Grab the --log=LEVEL logging option (if it exists).
    check_usage(args)
    if args[0].startswith('--log='):
        level = args[0][len('--log='):]
        logging.basicConfig(level=getattr(logging, level.upper(), None))
        args = args[1:]


    # Parse the JSON problem description and run the solver.
    check_usage(args)
    with open(args[0]) as problem_file:
        problem = json.loads(problem_file.read())
        start = problem['start']
        finish = problem['finish']
        ops = problem['ops']
        for action in gps(start, finish, ops):
            print action
    

if __name__ == '__main__':
    main(sys.argv[1:])
