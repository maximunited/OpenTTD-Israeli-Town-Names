"""Conservative page-size completion detection; HTTP errors always propagate."""
import logging


def collect_pages(year, fetch_page, parse_page, page_size=250, max_pages=100):
    records, seen = [], set()
    size_confirmed = False
    for page in range(1, max_pages + 1):
        batch = parse_page(fetch_page(page, year))
        logging.getLogger(__name__).warning('CBS page %s: %s records; cumulative %s; requested page size %s', page, len(batch), len(records) + len(batch), page_size)
        if len(batch) > page_size:
            raise ValueError('CBS returned more records than requested')
        for row in batch:
            key = (row['id'], row['year'])
            if key in seen:
                raise ValueError('Duplicate locality/year or repeated page; snapshot rejected')
            seen.add(key)
            records.append(row)
        if not batch:
            return records
        if len(batch) == page_size:
            size_confirmed = True
        elif size_confirmed:
            logging.getLogger(__name__).warning('CBS completed on partial page %s after observed full-size page(s)', page)
            return records
    raise ValueError('CBS pagination did not terminate')
