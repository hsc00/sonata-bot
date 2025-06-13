import asyncio
import csv
import os

from cogs.ratings import RatingsCog

folder_path = "./ratings"


async def import_ratings():
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        if os.path.isfile(full_path):
            print("File:", full_path)

            with open(full_path, encoding="utf-8") as f:
                content = f.read()

                user_id = int(filename.split(".")[0])
                rows = list(csv.DictReader(content.splitlines()))

                for row in rows:
                    try:
                        await RatingsCog.import_rating(user_id, row)

                    except:
                        continue


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(import_ratings())
