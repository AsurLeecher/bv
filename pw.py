import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
import logging

@Client.on_message(filters.command(["pw"]))
async def account_login(client: Client, message: Message):
    try:
        # Initial setup
        editable = await message.reply_text("Send **Auth code** in this format: **AUTH CODE**")
        auth_input = await client.listen(message.chat.id)
        auth_token = auth_input.text

        headers = {
            'authorization': f"Bearer {auth_token}",
            'client-id': '5eb393ee95fab7468a79d189',
            'client-version': '12.84',
            'user-agent': 'Android',
            'device-meta': '{APP_VERSION:12.84,DEVICE_MAKE:Asus,DEVICE_MODEL:ASUS_X00TD,OS_VERSION:6,PACKAGE_NAME:xyz.penpencil.physicswalb}',
            'content-type': 'application/json; charset=UTF-8',
        }

        # Fetch batches
        await editable.edit("Fetching your batches...")
        batches = await fetch_batches(headers)
        batch_list = "\n".join([f"`{batch['_id']}`: {batch['name']}" for batch in batches])
        await message.reply_text(f"**Available Batches:**\n{batch_list}")

        # Get batch ID
        editable = await message.reply_text("Send the **Batch ID** to download:")
        batch_input = await client.listen(message.chat.id)
        batch_id = batch_input.text

        # Fetch subjects
        await editable.edit("Fetching subjects...")
        subjects = await fetch_subjects(headers, batch_id)
        subject_ids = "&".join([subj['_id'] for subj in subjects])
        await message.reply_text(f"Subject IDs concatenated:\n`{subject_ids}`")

        # Get thumbnail
        editable = await message.reply_text("Send thumbnail URL (or 'no'):")
        thumb_input = await client.listen(message.chat.id)
        thumb_url = thumb_input.text
        thumbnail = await download_thumbnail(thumb_url) if thumb_url.lower() != 'no' else None

        # Process subjects
        await editable.edit("Processing content...")
        batch_name = next((batch['name'] for batch in batches if batch['_id'] == batch_id), "unknown_batch")
        output_file = f"{batch_name.replace(' ', '_')}.txt"

        with open(output_file, 'w') as f:
            for subject in subjects:
                for page in range(1, 5):  # Assuming 4 pages max
                    content = await fetch_content(headers, batch_id, subject['_id'], page)
                    if content:
                        for item in content:
                            if item.get('url'):
                                modified_url = item['url'].replace("d1d34p8vz63oiq", "d26g5bnklkwsh4").replace("mpd", "m3u8")
                                f.write(f"{item.get('topic', 'Untitled')}:{modified_url}\n")

        # Send final document
        await message.reply_document(
            document=output_file,
            thumb=thumbnail,
            caption=f"Content list for {batch_name}"
        )

        # Cleanup
        if thumbnail and os.path.exists(thumbnail):
            os.remove(thumbnail)
        os.remove(output_file)

    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
        logging.error(str(e))

async def fetch_batches(headers):
    response = requests.get(
        'https://api.penpencil.xyz/v3/batches/my-batches',
        params={'mode': '1', 'filter': 'false', 'limit': '20', 'page': '1'},
        headers=headers
    )
    return response.json().get('data', [])

async def fetch_subjects(headers, batch_id):
    response = requests.get(
        f'https://api.penpencil.xyz/v3/batches/{batch_id}/details',
        headers=headers
    )
    return response.json().get('data', {}).get('subjects', [])

async def fetch_content(headers, batch_id, subject_id, page):
    try:
        response = requests.get(
            f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents',
            params={'page': page, 'contentType': 'exercises-notes-videos'},
            headers=headers
        )
        return response.json().get('data', [])
    except Exception as e:
        logging.error(f"Error fetching page {page}: {str(e)}")
        return []

async def download_thumbnail(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open('thumb.jpg', 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return 'thumb.jpg'
    except Exception as e:
        logging.error(f"Thumbnail download failed: {str(e)}")
    return None
