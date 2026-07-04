import csv, json, os, sys, requests

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'collected_leads', 'leads.csv')
API_URL = 'http://127.0.0.1:8800/api/lead/status'


def load_leads(show_all=False):
    if not os.path.exists(CSV_PATH):
        print("No leads file found.")
        return []

    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    if not show_all:
        leads = [l for l in leads if l.get('status', '').strip().lower() == 'new']

    return leads


def display_leads(leads):
    if not leads:
        print("\nNo leads available to qualify.")
        return

    print(f"\n{'#':<4} {'Score':<6} {'Business Name':<35} {'Phone':<18} {'Category':<20}")
    print('-' * 90)
    for i, l in enumerate(leads, 1):
        name = l.get('business_name', '') or 'Unknown'
        name = name[:34]
        score = l.get('qualification_score', '-')
        phone = l.get('phone', '') or '-'
        phone = phone[:17]
        cat = l.get('category', '') or '-'
        cat = cat[:19].replace('\n', ' ')
        print(f"{i:<4} {score:<6} {name:<35} {phone:<18} {cat:<20}")


def qualify_lead(lead):
    page_url = lead.get('page_url', '').strip()
    if not page_url:
        print("  SKIPPED: No page_url")
        return False

    resp = requests.post(API_URL, json={
        'page_url': page_url,
        'status': 'qualified',
    }, timeout=5)
    data = resp.json()

    if data.get('status') == 'updated':
        name = lead.get('business_name', 'Unknown')
        print(f"  ✅ QUALIFIED: {name}")
        return True
    else:
        print(f"  ❌ Error: {data.get('error', 'Unknown')}")
        return False


def main():
    show_all = '--all' in sys.argv

    while True:
        leads = load_leads(show_all=show_all)
        if not leads:
            print("\nNo leads to qualify. Run a search first.")
            break

        display_leads(leads)

        print()
        choice = input("Enter number to qualify (or 'q' to quit, 'a' for all leads): ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'a':
            show_all = not show_all
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(leads):
                qualify_lead(leads[idx])
            else:
                print(f"  Invalid number. Pick 1-{len(leads)}")
        except ValueError:
            print("  Enter a number or 'q'")

    print("Done.")


if __name__ == '__main__':
    main()
