"""Run the onboarding flow on synthetic deals and print what happened.

    python demo.py
"""
import copy
import json
import pathlib

from pipeline import FakeCRM, FakeChat, FakeERP, FakeTickets, Onboarding

DATA = pathlib.Path(__file__).parent / "data"


def build() -> Onboarding:
    bundles = json.loads((DATA / "opportunities.json").read_text())
    customers = json.loads((DATA / "erp_customers.json").read_text())
    return Onboarding(FakeCRM(bundles), FakeTickets(), FakeERP(customers), FakeChat())


def main() -> None:
    flow = build()
    for opp in ["O-1", "O-2", "O-3", "O-4", "O-5"]:
        state = flow.handle_closed_won(opp)
        print(f"{opp}: {state['status'] or 'ignored (not closed won)'}  {state['log'][-1] if state['log'] else ''}")
    print(f"\nERP writes so far: {len(flow.erp.writes)}  (nothing is created before a person approves)")
    print(f"Tickets opened: {[t['id'] + ' for ' + t['opp'] for t in flow.tickets.tickets]}")
    print(flow.tickets.tickets[0]["body"] if flow.tickets.tickets else "")

    flow.handle_closed_won("O-1")  # the same event again
    print("\nO-1 triggered a second time ->", flow.states["O-1"]["log"][-1])
    flow.decide("O-1", "finance.lead@example.com", "approve")
    flow.handle_closed_won("O-1")
    print("O-1 approved, then triggered again ->", flow.states["O-1"]["log"][-1], f"| ERP writes: {len(flow.erp.writes)}")
    print("Chat:", flow.chat.messages)


if __name__ == "__main__":
    main()
