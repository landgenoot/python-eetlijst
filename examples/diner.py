#!/usr/bin/env python

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

import eetlijst
import sys

def main():
    if len(sys.argv) != 4:
        sys.stdout.write("Usage: %s <username> <password> <get>\n" % sys.argv[0])
        return 0

    # Parse action
    action = sys.argv[3].lower()

    if action not in ["get"]:
        sys.stdout.write("Invalid action: %s\n" % action)
        return 1

    # Create a client
    try:
        client = eetlijst.Eetlijst(username=sys.argv[1], password=sys.argv[2], login=True)
    except eetlijst.LoginError:
        sys.stderr.write("Username and/or password incorrect\n")
        return 1

    # Perform action
    if action == "get":
        get_action(client)

    return 0

def get_action(client):
    residents = client.get_residents()
    row = client.get_statuses(limit=1)[0]

    # Print a small header
    sys.stdout.write("Diner status for %s. " % row.date)

    if row.deadline:
        if row.has_deadline_passed():
            sys.stdout.write("The deadline is %s, and has passed.\n\n" % row.deadline.time())
        else:
            sys.stdout.write("The deadline is %s, so there is %s left.\n\n" % (row.deadline.time(), row.time_left()))
    else:
        sys.stdout.write("There is no deadline.\n\n")

    # Print the status as a horizontal list
    names = []
    values = []

    for name, status in zip(residents, row.statuses):
        # Convert to meaningful representation
        if status.value == 0:
            value = "X"
        elif status.value == -5:
            value = "?"
        elif status.value == 1:
            value = "C"
        elif status.value == -1:
            value = "D"
        elif status.value > 1:
            value = "C + %d" % (status.value - 1)
        elif status.value < -1:
            value = "D + %d" % (-1 * status.value - 1)

        # Add to rows
        width = max(len(name), len(value))

        names.append(name.center(width))
        values.append(value.center(width))

    # Print it all
    sys.stdout.write("In total, %d people (including guests) will attend diner.\n\n" % row.get_count())

    sys.stdout.write(" | ".join(names) + "\n")
    sys.stdout.write(" | ".join(values) + "\n\n")

    sys.stdout.write("X = No, C = Cook, D = Diner, ? = Unknown\n")

# E.g. `diner.py username password get'
if __name__ == "__main__":
    sys.exit(main())