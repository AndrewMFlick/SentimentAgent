# Feature Specification: Admin Sentiment Reanalysis & Tool Categorization

**Feature Branch**: `013-admin-feature-to`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: Admin feature to rerun sentiment analysis against available data and categorize it into tools. Should run ad hoc or triggered by tool status changes (new, merge, etc.)

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Manual Ad-Hoc Tool Recategorization (Priority: P1)

As an admin, I need to manually trigger sentiment reanalysis to backfill tool categorization in existing historical data, so that previously collected Reddit posts and comments can be associated with the correct tools for analysis and reporting.

**Why this priority**: This is the most critical user story because it addresses the immediate data gap - existing sentiment data exists but lacks tool associations. Without this, the Hot Topics feature and tool-specific dashboards cannot function properly with historical data. This delivers immediate value by making existing data useful.

**Independent Test**: Can be fully tested by triggering a reanalysis job via API/admin UI and verifying that sentiment_scores documents are updated with detected_tool_ids based on content analysis. Delivers value by making historical data queryable by tool.

**Acceptance Scenarios**:

1. **Given** an admin is authenticated with proper permissions, **When** they trigger a manual reanalysis job, **Then** the system queues all sentiment_scores documents without detected_tool_ids for reprocessing
2. **Given** a reanalysis job is running, **When** each sentiment score is processed, **Then** the system re-runs tool detection logic against the original post/comment content and updates the detected_tool_ids array
3. **Given** a reanalysis job completes, **When** the admin views the job results, **Then** they see statistics showing total documents processed, tools detected per document, and any errors encountered
4. **Given** sentiment data has been recategorized, **When** a user queries Hot Topics or tool-specific dashboards, **Then** they see results including the newly categorized historical data

---

### User Story 2 - Automatic Recategorization on Tool Status Changes (Priority: P2)

As an admin, when I create, merge, or modify tools in the system, I need sentiment data to be automatically recategorized to reflect the new tool configuration, so that analytics remain accurate without manual intervention.

**Why this priority**: This provides ongoing data quality maintenance and reduces admin burden. While less critical than the initial backfill (P1), it ensures data consistency as the tool catalog evolves. Without this, every tool change would require manual reanalysis.

**Independent Test**: Can be fully tested by creating a new tool, triggering the automatic recategorization, and verifying that relevant sentiment_scores documents are updated. Delivers value by maintaining data quality automatically.

**Acceptance Scenarios**:

1. **Given** an admin creates a new tool, **When** the tool is saved with status='active', **Then** the system automatically triggers a reanalysis job to find historical posts mentioning this tool
2. **Given** an admin merges two tools (Tool A → Tool B), **When** the merge completes, **Then** all sentiment_scores with detected_tool_ids containing Tool A are updated to reference Tool B instead
3. **Given** an admin changes a tool from archived to active, **When** the status change is saved, **Then** the system triggers reanalysis to detect mentions of the newly active tool
4. **Given** automatic recategorization is triggered, **When** the job completes, **Then** the admin receives a notification with job statistics

---

### User Story 3 - Recategorization Monitoring & Progress Tracking (Priority: P3)

As an admin, I need to monitor the progress of long-running reanalysis jobs and view detailed statistics about recategorization operations, so that I can ensure data quality and troubleshoot issues when they arise.

**Why this priority**: This is a quality-of-life improvement for admins managing large datasets. While important for operational visibility, the core functionality works without it. Users can still trigger jobs and see results, just without real-time progress.

**Independent Test**: Can be fully tested by starting a reanalysis job on a large dataset and monitoring the progress UI/API. Delivers value by providing operational visibility into batch processing.

**Acceptance Scenarios**:

1. **Given** a reanalysis job is running, **When** the admin views the job status page, **Then** they see real-time progress including percentage complete, documents processed, documents remaining, and estimated time remaining
2. **Given** multiple reanalysis jobs exist, **When** the admin views the job history, **Then** they see a list of all jobs with status (queued/running/completed/failed), start time, end time, and summary statistics
3. **Given** a reanalysis job encounters errors, **When** the admin views the job details, **Then** they see specific error messages, affected document IDs, and suggested remediation steps
4. **Given** a reanalysis job completes, **When** the admin views the job results, **Then** they see a breakdown of tools detected (e.g., "GitHub Copilot: 245 posts, Claude: 123 posts") and documents that couldn't be categorized

---

### Edge Cases

- **What happens when a reanalysis job is triggered while another is already running?**  
  System queues the new job to run after the current one completes, or rejects it with a "Job already in progress" error depending on configuration.

- **How does the system handle sentiment scores for deleted posts/comments?**  
  Reanalysis processes all sentiment_scores regardless of whether the original post/comment still exists in the database. Deleted content is skipped if content is unavailable.

- **What if tool detection logic changes after initial analysis?**  
  Reanalysis uses the current tool detection algorithm, which may yield different results than the original analysis. This is expected behavior - reanalysis should bring historical data up to current detection standards.

- **How does the system handle rate limits or API throttling during batch processing?**  
  Batch processing includes configurable rate limiting and retry logic with exponential backoff. Jobs pause and resume gracefully if rate limits are hit.

- **What if a sentiment score has no detectable tools after reanalysis?**  
  The detected_tool_ids array remains empty (or is set to empty if previously populated). This is valid - not all posts mention specific tools.

- **How are circular tool merges prevented?**  
  Tool merge validation (from Feature 011) prevents circular aliases. Reanalysis follows the alias chain to resolve to the primary tool.

- **What happens if a reanalysis job fails midway through processing?**  
  Jobs are idempotent - they can be safely rerun. Progress is checkpointed periodically so failed jobs can resume from the last checkpoint rather than starting over.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an admin API endpoint to trigger manual reanalysis jobs with optional parameters for date range, specific tools, or full dataset
- **FR-002**: System MUST re-run tool detection logic against original post/comment content when reanalyzing sentiment scores
- **FR-003**: System MUST update sentiment_scores documents with detected_tool_ids array based on current tool detection algorithms
- **FR-004**: System MUST automatically trigger reanalysis when tool status changes to 'active' or when new tools are created
- **FR-005**: System MUST automatically update sentiment_scores when tools are merged, replacing source tool IDs with target tool ID
- **FR-006**: System MUST process reanalysis jobs asynchronously without blocking API responses
- **FR-007**: System MUST track reanalysis job status (queued/running/completed/failed) with start time, end time, and progress percentage
- **FR-008**: System MUST log all reanalysis operations with admin user, timestamp, parameters, and results
- **FR-009**: System MUST be idempotent - reanalysis can be safely run multiple times on the same data
- **FR-010**: System MUST handle errors gracefully, logging failures without stopping the entire job
- **FR-011**: System MUST provide job statistics including total documents processed, tools detected per document, and error counts
- **FR-012**: Admin users MUST be authenticated and authorized before triggering reanalysis jobs
- **FR-013**: System MUST checkpoint progress periodically to enable job resumption after failures
- **FR-014**: System MUST respect rate limits when processing large batches of sentiment scores
- **FR-015**: System MUST resolve tool aliases to primary tools when updating detected_tool_ids (following alias chains from Feature 011)

### Key Entities

- **ReanalysisJob**: Represents a batch processing job for recategorizing sentiment data
  - Attributes: job_id, status, trigger_type (manual/automatic), triggered_by (admin user), parameters (date_range, tool_ids, batch_size), progress (processed_count, total_count, percentage), start_time, end_time, statistics (tools_detected, errors), error_log
  - Relationships: Associated with admin user who triggered it, references sentiment_scores being processed

- **SentimentScore** (existing, updated): Sentiment analysis results for Reddit posts/comments
  - New/Updated Attributes: detected_tool_ids (array of tool IDs found in content), last_analyzed_at (timestamp of most recent analysis), analysis_version (to track detection algorithm version)
  - Relationships: Links to Tools via detected_tool_ids array

- **Tool** (existing, updated): AI tools being tracked
  - Updated Behavior: Status changes trigger reanalysis jobs automatically
  - Merge Operations: When merged, trigger reanalysis to update detected_tool_ids

- **AdminAuditLog** (existing, extended): Audit trail for admin actions
  - New Event Types: reanalysis_triggered, reanalysis_completed, reanalysis_failed
  - Attributes: Include job_id, parameters, statistics in log entries

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admins can successfully trigger a reanalysis job via API and receive confirmation with job ID within 2 seconds
- **SC-002**: Reanalysis job processes sentiment_scores at minimum rate of 100 documents per second
- **SC-003**: At least 95% of sentiment_scores without detected_tool_ids are successfully categorized after full reanalysis
- **SC-004**: Tool merge operations automatically update all affected sentiment_scores within 1 hour for datasets up to 10,000 documents
- **SC-005**: New tool creation triggers automatic reanalysis and completes detection of historical mentions within 24 hours
- **SC-006**: Job status API provides progress updates with <5 second latency during active processing
- **SC-007**: Failed reanalysis jobs can be resumed from last checkpoint without reprocessing already-completed documents
- **SC-008**: Zero data loss during reanalysis - all sentiment_scores retain original data with only detected_tool_ids updated
- **SC-009**: Admin audit log captures 100% of reanalysis operations with full context (user, parameters, results)
- **SC-010**: Hot Topics feature displays accurate data including recategorized historical posts within 1 minute of job completion
