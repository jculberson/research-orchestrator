/* ============================================================================
   PROPOSED POLARIS READ-ONLY VIEWS  —  "Library Magic Assistant" data layer
   ----------------------------------------------------------------------------
   Target:  Microsoft SQL Server (Polaris ILS runs on SQL Server; the production
            database is named `Polaris`, primary schema `Polaris`).
   Purpose: Give the assistant ONE clean, READ-ONLY, PII-FREE surface to iterate
            over — title metadata, real-time per-branch availability, hold demand,
            new arrivals, and a denormalized "discovery" blob for embeddings/RAG.

   GUARDRAILS BAKED IN
   -------------------
   * All objects live in a separate `ai` schema (never touch base tables).
   * No patron / circulation-transaction / financial tables are referenced.
     Hold "demand" is exposed only as an aggregate COUNT — never who placed it.
   * Intended to be deployed on a READ REPLICA / reporting copy of Polaris
     (e.g. a database `PolarisReporting`), not the live transactional database.
   * A dedicated login is granted SELECT on schema `ai` only (see bottom).

   IMPORTANT — VERIFY AGAINST YOUR SCHEMA
   --------------------------------------
   Column/table names below match common Polaris 6.x/7.x schemas, but exact
   names drift between releases. Lines marked  -- VERIFY  should be confirmed
   with the discovery query in section 0 before go-live. Treat this as a
   well-grounded PROPOSAL to hand to whoever administers Polaris.
   ============================================================================ */


/* =========================================================================
   0.  SCHEMA DISCOVERY — run first to confirm real table/column names
   ========================================================================= */
-- List candidate tables:
--   SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
--   WHERE TABLE_NAME IN ('CircItemRecords','BibliographicRecords','Organizations',
--     'ItemStatuses','MaterialTypes','Collections','ShelfLocations',
--     'SysHoldRequests','BibliographicTags','BibliographicSubfields',
--     'MARCTypeOfMaterial') ORDER BY TABLE_NAME;
-- Inspect a table's columns:
--   SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
--   WHERE TABLE_NAME = 'CircItemRecords' ORDER BY ORDINAL_POSITION;


/* =========================================================================
   1.  SCHEMA + (optional) ITEM-STATUS POLICY
   ========================================================================= */
IF SCHEMA_ID('ai') IS NULL EXEC('CREATE SCHEMA ai');
GO

/* Which item statuses count as "available to walk up and grab today".
   Confirm the wording with the library — typically just 'In'. Others such as
   'In-Transit', 'Held', 'Out', 'In-Repair', 'Missing' are NOT shelf-available. */
CREATE OR ALTER VIEW ai.vwItemStatus AS
    SELECT  ist.ItemStatusID,
            ist.Description                              AS status_name,
            CAST(CASE WHEN ist.Description IN ('In')     -- VERIFY policy with library
                      THEN 1 ELSE 0 END AS bit)          AS is_shelf_available
    FROM    Polaris.ItemStatuses ist;
GO


/* =========================================================================
   2.  REFERENCE / LOOKUP VIEWS  (small, cacheable)
   ========================================================================= */

-- Branches (OrganizationCodeID: 1=System, 2=Library, 3=Branch -- VERIFY)
CREATE OR ALTER VIEW ai.vwBranch AS
    SELECT  o.OrganizationID                             AS branch_id,
            o.Name                                       AS branch_name,
            o.Abbreviation                               AS branch_code,
            o.SA_Address1                                AS address,        -- VERIFY
            o.SA_City                                    AS city,           -- VERIFY
            o.SA_PostalCode                              AS postal_code,    -- VERIFY
            o.SA_PhoneVoice1                             AS phone           -- VERIFY
    FROM    Polaris.Organizations o
    WHERE   o.OrganizationCodeID = 3;                                       -- VERIFY
GO

CREATE OR ALTER VIEW ai.vwMaterialType AS
    SELECT mt.MaterialTypeID AS material_type_id, mt.Description AS material_type
    FROM   Polaris.MaterialTypes mt;
GO

CREATE OR ALTER VIEW ai.vwCollection AS
    SELECT c.CollectionID AS collection_id, c.Name AS collection_name, c.OrganizationID AS branch_id
    FROM   Polaris.Collections c;
GO

CREATE OR ALTER VIEW ai.vwShelfLocation AS
    SELECT s.ShelfLocationID AS shelf_location_id, s.Description AS shelf_location, s.OrganizationID AS branch_id
    FROM   Polaris.ShelfLocations s;
GO

/* Branch hours. Polaris stores closure/open data for due-date math, but the
   table layout varies a lot by site. Hours change rarely, so the pragmatic
   option is a tiny maintained config table the assistant reads. Proposed shape: */
-- CREATE TABLE ai.BranchHours (branch_id int, day_of_week tinyint, open_time time,
--                              close_time time, is_closed bit);
CREATE OR ALTER VIEW ai.vwBranchHours AS
    SELECT branch_id, day_of_week, open_time, close_time, is_closed
    FROM   ai.BranchHours;            -- maintained config (see note above)
GO


/* =========================================================================
   3.  TITLE (BIB) METADATA  —  "what is this thing?"
   MARC-derived fields (subjects, ISBN, summary, audience) are pulled with
   correlated subqueries against the tag/subfield tables.
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwTitle AS
    SELECT
        br.BibliographicRecordID                         AS bib_id,
        br.BrowseTitle                                   AS title,          -- VERIFY
        br.BrowseAuthor                                  AS author,         -- VERIFY
        tom.Description                                  AS format,         -- type of material -- VERIFY
        br.CreationDate                                  AS added_date,
        /* ISBN: MARC 020 $a (first occurrence) */
        (SELECT TOP 1 sf.Data
           FROM Polaris.BibliographicTags t
           JOIN Polaris.BibliographicSubfields sf
                ON sf.BibliographicTagID = t.BibliographicTagID AND sf.Subfield = 'a'
          WHERE t.BibliographicRecordID = br.BibliographicRecordID
            AND t.TagNumber = 020)                       AS isbn,
        /* Publication date: MARC 264 $c, else 260 $c */
        (SELECT TOP 1 sf.Data
           FROM Polaris.BibliographicTags t
           JOIN Polaris.BibliographicSubfields sf
                ON sf.BibliographicTagID = t.BibliographicTagID AND sf.Subfield = 'c'
          WHERE t.BibliographicRecordID = br.BibliographicRecordID
            AND t.TagNumber IN (264,260)
          ORDER BY CASE t.TagNumber WHEN 264 THEN 0 ELSE 1 END)            AS published,
        /* Summary / annotation: MARC 520 $a */
        (SELECT TOP 1 sf.Data
           FROM Polaris.BibliographicTags t
           JOIN Polaris.BibliographicSubfields sf
                ON sf.BibliographicTagID = t.BibliographicTagID AND sf.Subfield = 'a'
          WHERE t.BibliographicRecordID = br.BibliographicRecordID
            AND t.TagNumber = 520)                       AS summary,
        /* Target audience / reading level: MARC 521 $a (e.g. "Ages 9-12") */
        (SELECT TOP 1 sf.Data
           FROM Polaris.BibliographicTags t
           JOIN Polaris.BibliographicSubfields sf
                ON sf.BibliographicTagID = t.BibliographicTagID AND sf.Subfield = 'a'
          WHERE t.BibliographicRecordID = br.BibliographicRecordID
            AND t.TagNumber = 521)                       AS audience,
        /* Subjects: all 6xx $a, semicolon-joined (SQL Server 2017+) */
        (SELECT STRING_AGG(CAST(sf.Data AS nvarchar(MAX)), '; ')
           FROM Polaris.BibliographicTags t
           JOIN Polaris.BibliographicSubfields sf
                ON sf.BibliographicTagID = t.BibliographicTagID AND sf.Subfield = 'a'
          WHERE t.BibliographicRecordID = br.BibliographicRecordID
            AND t.TagNumber IN (600,610,611,630,650,651)) AS subjects
    FROM Polaris.BibliographicRecords br
    LEFT JOIN Polaris.MARCTypeOfMaterial tom
           ON tom.MARCTypeOfMaterialID = br.PrimaryMARCTOMID               -- VERIFY
    WHERE br.RecordStatusID = 1;       -- final/active bibs only -- VERIFY
GO


/* =========================================================================
   4.  ITEM-LEVEL (copies)  —  no PII, no due-date/patron linkage
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwItem AS
    SELECT
        cir.ItemRecordID                                 AS item_id,
        cir.AssociatedBibRecordID                        AS bib_id,
        cir.AssignedBranchID                             AS branch_id,      -- shelving branch
        st.status_name                                   AS status,
        st.is_shelf_available                            AS is_available,
        cir.CallNumber                                   AS call_number,    -- VERIFY (may be parts)
        cir.MaterialTypeID                               AS material_type_id,
        cir.CollectionID                                 AS collection_id,
        cir.ShelfLocationID                              AS shelf_location_id,
        CAST(cir.HoldableFlag AS bit)                    AS holdable
    FROM Polaris.CircItemRecords cir
    JOIN ai.vwItemStatus st ON st.ItemStatusID = cir.ItemStatusID
    WHERE cir.RecordStatusID = 1            -- active items -- VERIFY
      AND cir.DisplayInPACFlag = 1;         -- only items shown in the public catalog -- VERIFY
GO


/* =========================================================================
   5.  REAL-TIME AVAILABILITY BY BRANCH  —  the table the tool iterates over
   "How many copies, and how many available, of bib X at each branch right now."
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwTitleAvailabilityByBranch AS
    SELECT
        i.bib_id,
        i.branch_id,
        b.branch_name,
        COUNT(*)                                         AS copies_total,
        SUM(CAST(i.is_available AS int))                 AS copies_available,
        SUM(CASE WHEN i.holdable = 1 THEN 1 ELSE 0 END)  AS copies_holdable
    FROM ai.vwItem i
    JOIN ai.vwBranch b ON b.branch_id = i.branch_id
    GROUP BY i.bib_id, i.branch_id, b.branch_name;
GO

/* System-wide rollup per title (drives the "X available now" badge) */
CREATE OR ALTER VIEW ai.vwTitleAvailability AS
    SELECT
        bib_id,
        SUM(copies_total)      AS copies_total,
        SUM(copies_available)  AS copies_available
    FROM ai.vwTitleAvailabilityByBranch
    GROUP BY bib_id;
GO


/* =========================================================================
   6.  HOLD DEMAND  —  aggregate only (drives "N holds ahead", NO patron data)
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwHoldDemand AS
    SELECT
        shr.BibliographicRecordID                        AS bib_id,
        COUNT(*)                                         AS active_holds
    FROM Polaris.SysHoldRequests shr
    JOIN Polaris.SysHoldStatuses hs ON hs.SysHoldStatusID = shr.SysHoldStatusID
    WHERE hs.Description IN ('Active','Pending','Held')   -- VERIFY open statuses
    GROUP BY shr.BibliographicRecordID;
GO


/* =========================================================================
   7.  NEW ARRIVALS  —  "what's new" (last 90 days)
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwNewArrivals AS
    SELECT TOP 500
        i.bib_id, t.title, t.author, t.format,
        MIN(c.added_date)                                AS first_added
    FROM ai.vwItem i
    JOIN ai.vwTitle t ON t.bib_id = i.bib_id
    JOIN Polaris.CircItemRecords c ON c.ItemRecordID = i.item_id
    WHERE c.FirstAvailableDate >= DATEADD(DAY, -90, GETDATE())              -- VERIFY
    GROUP BY i.bib_id, t.title, t.author, t.format
    ORDER BY first_added DESC;
GO


/* =========================================================================
   8.  DISCOVERY BLOB  —  one denormalized row per title for embeddings / RAG.
   This is the "repository for the tool to iterate over": the assistant (or a
   sync job) reads this, embeds `search_text`, and stores vectors downstream.
   ========================================================================= */
CREATE OR ALTER VIEW ai.vwTitleDiscovery AS
    SELECT
        t.bib_id,
        t.title, t.author, t.format, t.audience, t.published, t.isbn,
        t.subjects, t.summary,
        av.copies_total,
        av.copies_available,
        ISNULL(hd.active_holds, 0)                       AS active_holds,
        /* Compact, model-friendly text for embedding + keyword fallback */
        CONCAT_WS(' | ',
            t.title, t.author, t.format, t.audience, t.subjects, t.summary)  AS search_text
    FROM ai.vwTitle t
    LEFT JOIN ai.vwTitleAvailability av ON av.bib_id = t.bib_id
    LEFT JOIN ai.vwHoldDemand        hd ON hd.bib_id = t.bib_id;
GO


/* =========================================================================
   9.  EVENTS  —  usually NOT in Polaris
   Programs/story times typically live in LibCal, Communico, or the website CMS.
   Expose them through a sibling view over that source (or a synced table) so the
   assistant has one consistent interface. Proposed shape: */
-- CREATE TABLE ai.Events (event_id int, title nvarchar(200), branch_id int,
--   starts_at datetime2, ends_at datetime2, audience nvarchar(100),
--   description nvarchar(MAX), registration_url nvarchar(400));
CREATE OR ALTER VIEW ai.vwEvents AS
    SELECT e.event_id, e.title, e.branch_id, e.starts_at, e.ends_at,
           e.audience, e.description, e.registration_url
    FROM   ai.Events e;              -- fed from LibCal/Communico/CMS export
GO


/* =========================================================================
   10.  SECURITY  —  least-privilege read-only login for the assistant
   ========================================================================= */
-- On the reporting/replica server:
-- CREATE LOGIN magic_assistant_ro WITH PASSWORD = '<<strong-secret>>';
-- CREATE USER  magic_assistant_ro FOR LOGIN magic_assistant_ro;
-- GRANT SELECT ON SCHEMA::ai TO magic_assistant_ro;   -- ONLY the ai schema
-- DENY  SELECT ON SCHEMA::Polaris TO magic_assistant_ro;  -- never base tables
-- (No INSERT/UPDATE/DELETE/EXEC anywhere. Writes — holds/ILL — go exclusively
--  through Polaris's official authenticated APIs, not this connection.)


/* =========================================================================
   11.  PERFORMANCE / REFRESH NOTES
   * Availability changes constantly; query ai.vwTitleAvailabilityByBranch live
     against the replica for accuracy. If the replica lags, surface "as of HH:MM".
   * For the embedding pipeline, you do NOT need real-time: snapshot
     ai.vwTitleDiscovery nightly (or on bib change) into the vector store; refresh
     only `copies_available`/`active_holds` at query time from the live views.
   * If 6xx/STRING_AGG subqueries are heavy at scale, materialize vwTitle into a
     nightly table (ai.TitleCache) and point vwTitleDiscovery at it.
   ========================================================================= */
