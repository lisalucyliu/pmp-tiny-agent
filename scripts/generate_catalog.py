"""One-off script that generates data/catalog.json from the product table.

Run once with: python scripts/generate_catalog.py
Not used by the agent at runtime - the agent just reads the JSON file
this script produces.
"""

import json
import random
import string
from pathlib import Path

ROWS = [
    # vendor, name, type, description, engineering, finance
    ("Watchtail", "Watchtail Enterprise", "SaaS",
     "Observability and security platform for large companies: metrics, logs, traces, and database monitoring",
     "N", "N"),
    ("Watchtail", "Watchtail Pro", "SaaS",
     "The same platform for smaller teams including database monitoring", "A", "N"),
    ("Watchtail", "Watchtail Agent", "AMI",
     "Monitoring agent preinstalled on an EC2 image", "A", "N"),
    ("Watchtail", "Watchtail Operator", "Container",
     "Installs and manages the Watchtail agent on Kubernetes", "N", "N"),
    ("Sentrypoint Security", "Managed Watchtail Threat Detection", "Professional services",
     "24/7 managed security service that runs on Watchtail threat detection", "N", "N"),
    ("Ironveil", "Ironveil Cloud Guard", "SaaS",
     "RETIRED. Customers moved to Ironveil Horizon", "A", "A"),
    ("Ironveil", "Ironveil Horizon", "SaaS",
     "AI security platform that predicts and responds to threats across AWS and multicloud", "N", "N"),
    ("Lakeforge", "Lakeforge Data Platform", "SaaS",
     "Unified data and AI platform with a 14-day free trial", "A", "A"),
    ("Talonix", "Talonix Platform", "SaaS",
     "AI protection for devices identities and cloud through one agent", "A", "A"),
    ("QuarryDB", "QuarryDB Cloud (pay-as-you-go)", "SaaS",
     "Fully managed NoSQL database with vector search", "N", "N"),
    ("QuarryDB", "QuarryDB Multimodal Embeddings", "Machine learning",
     "Turns text and images into vectors for search", "N", "N"),
    ("Gatekey", "Gatekey Workforce Starter", "SaaS",
     "Identity and access for employees contractors and partners", "A", "A"),
    ("Vaultline", "Vaultline Business", "SaaS",
     "Enterprise password manager", "A", "A"),
    ("Meshwire", "Meshwire", "SaaS",
     "Secure networking that replaces legacy VPNs", "N", "N"),
    ("Auditlane", "Auditlane", "SaaS",
     "Compliance and security automation", "N", "N"),
    ("Tunnelport", "Tunnelport Access Server (BYOL)", "AMI",
     "Self-hosted business VPN on EC2", "A", "N"),
    ("Bastion Networks", "Bastion NGFW VM", "AMI",
     "Next-generation firewall for AWS networks", "N", "N"),
    ("Cardinal Linux", "Cardinal Enterprise Linux for SAP", "AMI",
     "Enterprise Linux for SAP with high availability", "N", "N"),
    ("Searchloom", "Searchloom Search API", "AI agents and tools",
     "Web search API for developers and AI apps", "N", "N"),
    ("Parsewell AI", "Parsewell Document Agent", "AI agents and tools",
     "Pulls structured data out of messy documents", "N", "N"),
    ("Tasklane", "Tasklane MCP Server", "AI agents and tools",
     "Lets AI assistants read and update Tasklane projects", "A", "N"),
    ("BucketShield", "BucketShield Malware Scanning", "Container",
     "Scans S3 and other AWS storage for malware", "A", "A"),
    ("Rankwise AI", "Rankwise Rerank 3", "Machine learning",
     "Re-sorts search results by meaning", "N", "N"),
    ("Lumora Labs", "Lumora Image Large", "Machine learning",
     "Image generation model", "D", "N"),
    ("Holdfast Security", "Holdfast Incident Response Retainer", "Professional services",
     "On-call incident response team", "N", "N"),
    ("Identiweave", "Identiweave Identity Resolution", "Data",
     "Connects customer records across sources for analytics", "N", "N"),
    ("Larkspur Linux", "Larkspur Linux 22.04 LTS", "Free",
     "Free general-purpose Linux", "A", "A"),
    ("Breachkit", "Breachkit Linux", "Free",
     "Linux for penetration testing and security research", "D", "D"),
]


def make_product_id(used: set) -> str:
    while True:
        candidate = "prod-" + "".join(random.choices(string.ascii_lowercase, k=8))
        if candidate not in used:
            used.add(candidate)
            return candidate


def main():
    used_ids = set()
    products = []
    for vendor, name, type_, description, eng, fin in ROWS:
        product_id = make_product_id(used_ids)
        products.append({
            "product_id": product_id,
            "vendor": vendor,
            "name": name,
            "type": type_,
            "description": description,
            "link": f"https://example.com/marketplace/{product_id}",
            "approval": {"Engineering": eng, "Finance": fin},
        })

    out_path = Path(__file__).parent.parent / "data" / "catalog.json"
    out_path.write_text(json.dumps(products, indent=2) + "\n")
    print(f"Wrote {len(products)} products to {out_path}")


if __name__ == "__main__":
    main()
