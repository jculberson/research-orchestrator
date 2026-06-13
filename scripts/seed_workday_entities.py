"""One-off seed script for the Workday intelligence entity set.

Run with: .venv/Scripts/python scripts/seed_workday_entities.py

Safe to re-run for adjustments, but will create duplicate rows if an entity
with the same name already exists (no upsert) - check the `entities` table
in Studio before re-running, or delete existing rows first.
"""

from research_orchestrator.db.client import get_client, insert_entity

ENTITIES = [
    # --- The company itself, tracked via SEC EDGAR ---
    {
        "name": "Workday",
        "entity_type": "company",
        "query_template": "Workday Inc earnings news announcement",
        "cik": "1327811",
        "tags": ["company", "workday"],
        "metadata": {"filing_forms": ["8-K", "4"]},
    },
    # --- Officers / leadership ---
    {
        "name": "Carl Eschenbach",
        "entity_type": "officer",
        "query_template": "{name} Workday CEO",
        "tags": ["officer", "leadership"],
    },
    {
        "name": "Aneel Bhusri",
        "entity_type": "officer",
        "query_template": "{name} Workday",
        "tags": ["officer", "leadership", "founder"],
    },
    {
        "name": "David Duffield",
        "entity_type": "officer",
        "query_template": "{name} Workday",
        "tags": ["officer", "leadership", "founder"],
    },
    {
        "name": "Zane Rowe",
        "entity_type": "officer",
        "query_template": "{name} Workday CFO",
        "tags": ["officer", "leadership"],
    },
    # --- Partner ecosystem ---
    {
        "name": "Deloitte",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting"],
    },
    {
        "name": "Accenture",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting"],
    },
    {
        "name": "PwC",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting"],
    },
    {
        "name": "KPMG",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting"],
    },
    {
        "name": "Collaborative Solutions",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting"],
    },
    {
        "name": "IBM",
        "entity_type": "partner",
        "query_template": "{name} Workday partnership",
        "tags": ["partner", "consulting", "technology"],
    },
    # --- Competitors ---
    {
        "name": "SAP SuccessFactors",
        "entity_type": "competitor",
        "query_template": "{name} vs Workday HCM",
        "tags": ["competitor", "hcm"],
    },
    {
        "name": "Oracle Cloud HCM",
        "entity_type": "competitor",
        "query_template": "{name} vs Workday",
        "tags": ["competitor", "hcm"],
    },
    {
        "name": "ServiceNow",
        "entity_type": "competitor",
        "query_template": "{name} Workday competitor HR",
        "tags": ["competitor", "hcm"],
    },
    {
        "name": "UKG",
        "entity_type": "competitor",
        "query_template": "{name} vs Workday",
        "tags": ["competitor", "hcm"],
    },
    {
        "name": "Ceridian Dayforce",
        "entity_type": "competitor",
        "query_template": "{name} vs Workday",
        "tags": ["competitor", "hcm"],
    },
    # --- Broad topics covering ventures, events, market, customers ---
    {
        "name": "Workday Ventures",
        "entity_type": "topic",
        "query_template": "Workday Ventures investment startup",
        "tags": ["topic", "ventures"],
    },
    {
        "name": "Workday AI Agents",
        "entity_type": "topic",
        "query_template": "Workday AI agent announcement",
        "tags": ["topic", "product", "ai"],
    },
    {
        "name": "Workday Rising",
        "entity_type": "topic",
        "query_template": "Workday Rising conference event",
        "tags": ["topic", "events"],
    },
    {
        "name": "Workday User Group",
        "entity_type": "topic",
        "query_template": "Workday user group community WDUG",
        "tags": ["topic", "community"],
    },
    {
        "name": "Workday Acquisition",
        "entity_type": "topic",
        "query_template": "Workday acquisition merger acquires",
        "tags": ["topic", "m&a"],
    },
    {
        "name": "Workday Customers",
        "entity_type": "topic",
        "query_template": "Workday customer case study implementation",
        "tags": ["topic", "customers"],
    },
    {
        "name": "Workday Marketplace",
        "entity_type": "topic",
        "query_template": "Workday Marketplace partner app integration",
        "tags": ["topic", "ecosystem"],
    },
    {
        "name": "Workday Layoffs",
        "entity_type": "topic",
        "query_template": "Workday layoffs restructuring workforce",
        "tags": ["topic", "company-news"],
    },
]


def main() -> None:
    client = get_client()
    for entity in ENTITIES:
        row = insert_entity(
            client,
            name=entity["name"],
            entity_type=entity["entity_type"],
            query_template=entity.get("query_template"),
            cik=entity.get("cik"),
            tags=entity.get("tags", []),
            metadata=entity.get("metadata", {}),
        )
        print(f"Added {row['entity_type']:>10}: {row['name']}")


if __name__ == "__main__":
    main()
