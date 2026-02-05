import asyncio
import re
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, text

async def update_urls():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localdb:5432/upwork_processing')

    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT id, description FROM jobs'))
        updated_count = 0
        for job_id, description in result:
            matches = re.findall(r'https?://[^\s<>"\'\)]+', description)
            urls = []
            seen = set()
            
            for match in matches:
                url = match.rstrip('.,;:')
                if 'upwork.com' not in url.lower() and url not in seen:
                    seen.add(url)
                    urls.append(url)
            
            if urls:
                await conn.execute(
                    text("UPDATE jobs SET description_urls = :urls WHERE id = :id"),
                    {'urls': json.dumps(urls), 'id': job_id}
                )
                updated_count += 1

        url_counts = await conn.execute(text('SELECT COUNT(*) FROM jobs WHERE jsonb_array_length(description_urls) > 0'))
        count = url_counts.scalar()
        print(f'Total jobs with URLs: {count}')
        print(f'Total updated: {updated_count}')

asyncio.run(update_urls())