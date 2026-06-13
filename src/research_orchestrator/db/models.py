from dataclasses import dataclass, field


@dataclass
class Entity:
    id: str
    name: str
    entity_type: str
    query_template: str | None
    cik: str | None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    is_active: bool = True

    @classmethod
    def from_row(cls, row: dict) -> "Entity":
        return cls(
            id=row["id"],
            name=row["name"],
            entity_type=row["entity_type"],
            query_template=row.get("query_template"),
            cik=row.get("cik"),
            tags=row.get("tags", []),
            metadata=row.get("metadata", {}),
            is_active=row.get("is_active", True),
        )

    def search_query(self) -> str:
        if self.query_template:
            return self.query_template.format(name=self.name)
        return f"{self.name} Workday"


@dataclass
class Source:
    id: str
    name: str
    url: str
    source_type: str
    topic: str | None
    tags: list[str] = field(default_factory=list)
    scrape_config: dict = field(default_factory=dict)
    is_active: bool = True

    @classmethod
    def from_row(cls, row: dict) -> "Source":
        return cls(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            source_type=row["source_type"],
            topic=row.get("topic"),
            tags=row.get("tags", []),
            scrape_config=row.get("scrape_config", {}),
            is_active=row.get("is_active", True),
        )
