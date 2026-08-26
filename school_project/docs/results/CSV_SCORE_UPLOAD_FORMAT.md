# Result CSV Bulk Upload Format

The staff bulk score uploader accepts one CSV file for one class arm and one academic term.

## Required columns

```csv
admission_number,subject,ca_score,exam_score
MDS/2025/0001,Mathematics,25,68
MDS/2025/0002,Mathematics,24,61
```

- `admission_number` must belong to an active student in the selected class.
- `subject` is matched case-insensitively and is resolved against the selected class level.
- `ca_score` must be between 0 and 30.
- `exam_score` must be between 0 and 70.
- Duplicate student/subject rows are rejected.
- The complete file is validated before any row is written. If any row fails validation, **nothing is imported**.

## Excel

In Excel, save the sheet as **CSV UTF-8 (Comma delimited) (*.csv)** before uploading. Do not upload the school's locked legacy workbook directly.

## Ranking

After a successful import, the system recalculates:

1. each student's overall total and average;
2. class position using competition ranking (for example, 1st, 2nd, 2nd, 4th);
3. each subject's class average;
4. each student's position in each subject.

The same calculation service is also available through the admin action and the `recalculate_positions` management command.
