SEVERITY_ORDER = {'critical': 0, 'warning': 1, 'suggestion': 2, 'info': 3}


def filter_comments(comments: list[dict], max_total: int = 20) -> list[dict]:
    # Step 1 — remove low confidence
    filtered = [c for c in comments if c.get('confidence', 0) >= 0.6]

    # Step 2 — deduplicate same position + category
    seen = {}
    deduped = []
    for c in filtered:
        key = (c.get('position'), c.get('category'))
        if key in seen:
            existing_idx = seen[key]
            if c.get('confidence', 0) > deduped[existing_idx].get('confidence', 0):
                deduped[existing_idx] = c
        else:
            seen[key] = len(deduped)
            deduped.append(c)

    # Step 3 — sort by severity then confidence
    deduped.sort(key=lambda c: (
        SEVERITY_ORDER.get(c.get('severity', 'info'), 99),
        -c.get('confidence', 0)
    ))

    # Step 4 — cap at max_total
    return deduped[:max_total]